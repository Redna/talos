import os
import json
import sys

# Setup local import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from log_tail_tool import log_tail_structured

def test_log_tail_structured():
    """
    S-VERIFY for log_tail_structured.
    """
    print("Starting S-VERIFY for log_tail_structured...")
    
    test_file = "test_tail.log"
    with open(test_file, "w") as f:
        f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")

    # 1. Test basic tail
    res = log_tail_structured(test_file, lines=3)
    if res["status"] != "SUCCESS" or len(res["lines"]) != 3 or res["lines"][-1] != "line 5":
        print(f"FAILURE: Tail failed. Result: {res}")
        return False
    print("SUCCESS: Correctly retrieved last 3 lines.")

    # 2. Test file shorter than request
    res = log_tail_structured(test_file, lines=10)
    if len(res["lines"]) != 5:
        print(f"FAILURE: Tail failed on short file. Got {len(res['lines'])} lines.")
        return False
    print("SUCCESS: Handled short file correctly.")

    # 3. Test non-existent file
    res = log_tail_structured("missing.log")
    if res["status"] != "ERROR" or res["code"] != "FILE_NOT_FOUND":
        print(f"FAILURE: Did not detect missing file. {res}")
        return False
    print("SUCCESS: Handled missing file correctly.")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("S-VERIFY PASSED.")
    return True

if __name__ == "__main__":
    if test_log_tail_structured():
        exit(0)
    else:
        exit(1)
