#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions
"""

# JSON utilities
try:
    import orjson as json_lib
    
    def json_dumps(obj):
        return json_lib.dumps(obj).decode('utf-8')
    
    def json_loads(s):
        if isinstance(s, bytes):
            return json_lib.loads(s)
        return json_lib.loads(s.encode('utf-8'))
    
    JSON_USE_ORJSON = True
    
except ImportError:
    import json as json_lib
    
    def json_dumps(obj):
        return json_lib.dumps(obj, ensure_ascii=False)
    
    def json_loads(s):
        if isinstance(s, bytes):
            s = s.decode('utf-8')
        return json_lib.loads(s)
    
    JSON_USE_ORJSON = False


__all__ = ['json_dumps', 'json_loads', 'JSON_USE_ORJSON']
