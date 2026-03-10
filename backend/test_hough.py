import requests
import json

def test_hough_method(method_name):
    url = 'http://127.0.0.1:8090/cv/hough'
    files = {'image': open(r'c:\SmartConstructionManagement\Research_Project_25_26J_168\flutterApp\AppImages\tile.jpg', 'rb')}
    data = {'method': method_name}

    print(f'\n=== Testing {method_name.upper()} Hough Method ===')
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Success: {result["success"]}')
            print(f'📊 Method: {result["method"]}')
            print(f'🔢 Lines detected: {result["count"]}')
            print(f'⏱️  Processing time: {result["processing_time"]}s')

            if result['count'] > 0:
                print('📋 First few lines:')
                for line in result['lines'][:5]:  # Show first 5 lines
                    print(f'  Line {line["id"]}: ({line["start"][0]}, {line["start"][1]}) → ({line["end"][0]}, {line["end"][1]}) | Length: {line["length"]}px')
            else:
                print('⚠️  No lines detected')

            # Save the result image for inspection
            import base64
            with open(f'tile_{method_name}_result.jpg', 'wb') as f:
                f.write(base64.b64decode(result['image_b64']))
            print(f'💾 Result image saved as: tile_{method_name}_result.jpg')

        else:
            print(f'❌ Error: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'💥 Exception: {e}')

if __name__ == '__main__':
    # Test both methods
    test_hough_method('probabilistic')
    test_hough_method('standard')

    print('\n🎉 Testing complete!')