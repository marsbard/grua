#!/usr/bin/env python

#import grua

import unittest

BridgeIp='SOME VALUE'

def tpl_lookup(key):
    if key == 'BRIDGE_IP':
        return BridgeIp


def parse_template(tpl):
    a1 = tpl.split("<%")
    out=''
    for i in range(0,len(a1)):
        if i%2==1: # odd, replace template
            a2 = a1[i].split("%>")
            if len(a2) > 1:
                out += tpl_lookup(a2[0].strip())
                out += a2[1]
            else:
                out += a2[0]
        else: # even, use directly
            out += a1[i]

    return out

def get_value(dict, key):
    if not dict.has_key(key):
        return ''

    return parse_template(dict[key])

def test_replace():
    testdict=dict()
    testdict['test']='Hello <% BRIDGE_IP %>x'
    print "BridgeIp=" + BridgeIp
    value = get_value(testdict, 'test')
    print value

test_replace()
