##############################################################################
#
# redsky            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Christopher J. Wright
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
from functools import partial

import numpy as np
from numpy.testing import assert_array_equal

from ..savers import NPYSaver
from ..streamer import event_map, store_dec
import pytest
from itertools import islice


def test_streaming(exp_db, tmp_dir, start_uid1):
    dnsm = {'img': partial(NPYSaver, root=tmp_dir)}

    def f(img):
        return img * 2

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'img': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'img': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['img'],
                   })(f))

    input_hdr = exp_db[start_uid1]
    a = exp_db.restream(input_hdr, fill=True)
    s = False
    for (name, doc), (_, odoc) in zip(dec_f(img=a),
                                      exp_db.restream(input_hdr, fill=True)):
        if name == 'start':
            assert doc['parents'][0] == input_hdr['start']['uid']
            s = True
        if name == 'event':
            assert s is True
            assert isinstance(doc['data']['img'], np.ndarray)
            assert_array_equal(doc['data']['img'],
                               f(odoc['data']['pe1_image']))
        if name == 'stop':
            assert doc['exit_status'] == 'success'
    for ev1, ev2 in zip(exp_db.get_events(input_hdr, fill=True),
                        exp_db.get_events(exp_db[-1], fill=True)):
        assert_array_equal(f(ev1['data']['pe1_image']),
                           ev2['data']['img'])


def test_double_streaming(exp_db, tmp_dir, start_uid1):
    dnsm = {'pe1_image': partial(NPYSaver, root=tmp_dir)}

    def f(img):
        return img * 2

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'img': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'pe1_image': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['pe1_image'],
                   })(f))

    input_hdr = exp_db[start_uid1]
    a = exp_db.restream(input_hdr, fill=True)
    for (name, doc), (_, odoc) in zip(dec_f(img=dec_f(img=a)),
                                      exp_db.restream(input_hdr, fill=True)):
        if name == 'start':
            s = True
        if name == 'event':
            assert s is True
            assert isinstance(doc['data']['pe1_image'], np.ndarray)
            assert_array_equal(doc['data']['pe1_image'],
                               f(f((odoc['data']['pe1_image']))))
        if name == 'stop':
            assert doc['exit_status'] == 'success'
    for ev1, ev2 in zip(exp_db.get_events(input_hdr, fill=True),
                        exp_db.get_events(exp_db[-1], fill=True)):
        assert_array_equal(f(f(ev1['data']['pe1_image'])),
                           ev2['data']['pe1_image'])


def test_multi_stream(exp_db, tmp_dir, start_uid1):
    dnsm = {'img': partial(NPYSaver, root=tmp_dir)}

    def f(img1, img2):
        return img1 - img2

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'img1': {'name': 'primary', 'data_key': 'pe1_image'},
                   'img2': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'img': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['img'],
                   })(f))

    input_hdr = exp_db[start_uid1]
    a = exp_db.restream(input_hdr, fill=True)
    b = exp_db.restream(input_hdr, fill=True)
    s = False
    for (name, doc), (_, odoc) in zip(dec_f(img1=a, img2=b),
                                      exp_db.restream(input_hdr, fill=True)):
        if name == 'start':
            assert doc['parents'][0] == input_hdr['start']['uid']
            s = True
        if name == 'event':
            assert s is True
            assert isinstance(doc['data']['img'], np.ndarray)
            assert_array_equal(
                doc['data']['img'],
                f(odoc['data']['pe1_image'], odoc['data']['pe1_image']))
        if name == 'stop':
            assert doc['exit_status'] == 'success'
    for ev1, ev2 in zip(exp_db.get_events(input_hdr, fill=True),
                        exp_db.get_events(exp_db[-1], fill=True)):
        assert_array_equal(f(ev1['data']['pe1_image'],
                             ev1['data']['pe1_image']),
                           ev2['data']['img'])


def test_multi_output(exp_db, tmp_dir, start_uid1):
    dnsm = {'img1': partial(NPYSaver, root=tmp_dir),
            'img2': partial(NPYSaver, root=tmp_dir)}

    def f(img):
        return img * 2, img / 2

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'img': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'img1': {'dtype': 'array'},
                                 'img2': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['img1', 'img2'],
                   })(f))

    input_hdr = exp_db[start_uid1]
    a = exp_db.restream(input_hdr, fill=True)
    s = False
    for (name, doc), (_, odoc) in zip(dec_f(img=a),
                                      exp_db.restream(input_hdr, fill=True)):
        if name == 'start':
            assert doc['parents'][0] == input_hdr['start']['uid']
            s = True
        if name == 'event':
            assert s is True
            for k in ['img1', 'img2']:
                assert isinstance(doc['data'][k], np.ndarray)
            for x, y in zip([doc['data'][k] for k in ['img1', 'img2']],
                            f(odoc['data']['pe1_image'])):
                assert_array_equal(x, y)
        if name == 'stop':
            assert doc['exit_status'] == 'success'
    for ev1, ev2 in zip(exp_db.get_events(input_hdr, fill=True),
                        exp_db.get_events(exp_db[-1], fill=True)):
        for x, y in zip([ev2['data'][k] for k in ['img1', 'img2']],
                        f(ev1['data']['pe1_image'])):
            assert_array_equal(x, y)


@pytest.mark.xfail(strict=True, raises=RuntimeError)
def test_known_fail(exp_db, tmp_dir, start_uid1):
    dnsm = {'img': partial(NPYSaver, root=tmp_dir)}

    def f(img):
        img * 2
        raise RuntimeError('Known Fail')

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'img': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'img': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['img'],
                   })(f))

    input_hdr = exp_db[start_uid1]
    a = exp_db.restream(input_hdr, fill=True)
    s = False
    for (name, doc), (_, odoc) in zip(dec_f(img=a),
                                      exp_db.restream(input_hdr, fill=True)):
        if name == 'start':
            assert doc['parents'][0] == input_hdr['start']['uid']
            s = True
        if name == 'stop':
            assert s is True
            assert doc['exit_status'] == 'failure'
            assert doc['reason'] == repr(RuntimeError('Known Fail'))


@pytest.mark.xfail(strict=True, raises=RuntimeError)
def test_data_keys_fail(exp_db, tmp_dir, start_uid1):
    dnsm = {'img': partial(NPYSaver, root=tmp_dir)}

    def f(img):
        return img * 2

    store_dec(exp_db, dnsm)(
        event_map({'img': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'bad': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['img'],
                   })(f))


@pytest.mark.xfail(strict=True, raises=RuntimeError)
def test_input_keys_fail(exp_db, tmp_dir, start_uid1):
    dnsm = {'img': partial(NPYSaver, root=tmp_dir)}

    def f(img):
        return img * 2

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'bad': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'bad': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['bad'],
                   })(f))

    input_hdr = exp_db[start_uid1]
    a = exp_db.restream(input_hdr, fill=True)
    for (name, doc), (_, odoc) in zip(dec_f(img=a),
                                      exp_db.restream(input_hdr, fill=True)):
        pass


def test_multi_stream_remux(exp_db, tmp_dir, start_uid1, start_uid2):
    def remux(s1, s2, n=0):
        s1_start, s2_start = [next(s) for s in [s1, s2]]
        yield s1_start
        s1_desc, s2_desc = [next(s) for s in [s1, s2]]
        yield s1_desc

        # This is the part where we fast forward s1 to n
        cannonical_event = next(islice(s1, n, n + 1))
        for name, doc in s2:
            if name != 'event':
                break
            yield cannonical_event
        # This is the part where we fast forward to the end
        for name, doc in s1:
            if name == 'stop':
                yield name, doc

    remux_func = partial(remux, n=1)
    dnsm = {'img': partial(NPYSaver, root=tmp_dir)}

    def f(img1, img2):
        return img1 - img2

    dec_f = store_dec(exp_db, dnsm)(
        event_map({'img1': {'name': 'primary', 'data_key': 'pe1_image',
                            'remux': (remux_func, 'img2')},
                   'img2': {'name': 'primary', 'data_key': 'pe1_image'}},
                  {'data_keys': {'img': {'dtype': 'array'}},
                   'name': 'primary',
                   'returns': ['img'],
                   })(f))

    input_hdr1 = exp_db[start_uid1]
    input_hdr2 = exp_db[start_uid2]
    a = exp_db.restream(input_hdr1, fill=True)
    b = exp_db.restream(input_hdr2, fill=True)
    s = False

    # For testing purposes get the cannonical event
    z = exp_db.restream(input_hdr1, fill=True)
    ce = next(islice(z, 1 + 2, 1 + 3))[1]

    for (name, doc), (_, odoc) in zip(dec_f(img1=a, img2=b),
                                      exp_db.restream(input_hdr2, fill=True)):
        if name == 'start':
            assert input_hdr2['start']['uid'] in doc['parents']
            s = True
        if name == 'event':
            assert s is True
            assert isinstance(doc['data']['img'], np.ndarray)
            assert_array_equal(
                doc['data']['img'],
                f(odoc['data']['pe1_image'], ce['data']['pe1_image']))
        if name == 'stop':
            assert doc['exit_status'] == 'success'
    for ev1, ev2 in zip(exp_db.get_events(input_hdr2, fill=True),
                        exp_db.get_events(exp_db[-1], fill=True)):
        assert_array_equal(f(ev1['data']['pe1_image'],
                             ce['data']['pe1_image']),
                           ev2['data']['img'])


# TODO: write more tests
"""
2. Test subsampling
3. Test stream combining
"""
