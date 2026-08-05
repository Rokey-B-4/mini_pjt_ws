import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/rokey/mini_pjt_ws/install/mini_pjt_vision'
