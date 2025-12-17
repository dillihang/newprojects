import sys
import os
import tempfile
import base64 

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Devopsandcloudautomation', 'devopsEx15'))
import pushfiletogitviaapi


def test_get_file_content_func():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test content. this is just for test")
        temp_path = f.name

    result = pushfiletogitviaapi.get_file_content(temp_path)

    expected = base64.b64encode(b"test content. this is just for test").decode()

    assert result == expected

if __name__=="__main__":

    test_get_file_content_func()