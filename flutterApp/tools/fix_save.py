import sys

with open('lib/screens/upload_building_plan_screen.dart', 'rb') as f:
    data = f.read()

# Find the old block: from "Saving building structure<ellipsis>" through old pipelineStep=4 catch block
old = (
    b"ng building structure\xc3\xa2\xe2\x82\xac\xc2\xa6');\r\n"
    b"      await api.postBuildingStructure(\r\n"
    b"          widget.projectId, _wallingResult ?? <String, dynamic>{});\r\n"
    b"\r\n"
    b"      // Background: generate 3D views \xc3\xa2\xe2\x82\xac\xe2\x80\x9d non-fatal\r\n"
    b"      _generate3dInBackground(api);\r\n"
    b"\r\n"
    b"      if (!mounted) return;\r\n"
    b"      setState(() {\r\n"
    b"        _pipelineStep = 4;\r\n"
    b"        _loading = false;\r\n"
    b"        _status = '';\r\n"
    b"      });\r\n"
    b"    } catch (e) {"
)

new_block = (
    b"ng building structure...');\r\n"
    b"\r\n"
    b"      if (_sfResult != null) {\r\n"
    b"        setState(() => _status = 'Saving structural frame...');\r\n"
    b"        await api.postStructuralFrame(widget.projectId, <String, dynamic>{\r\n"
    b"          'output': <String, dynamic>{\r\n"
    b"            'units': (_sfResult!['output'] as Map?)?['units'],\r\n"
    b"            'totalColumns': (_sfResult!['output'] as Map?)?['totalColumns'],\r\n"
    b"          },\r\n"
    b"          'groundFloor': <String, dynamic>{\r\n"
    b"            'columns': (_sfResult!['groundFloor'] as Map?)?['columns'] ?? {},\r\n"
    b"          },\r\n"
    b"        });\r\n"
    b"      }\r\n"
    b"\r\n"
    b"      if (_finishingResult != null) {\r\n"
    b"        setState(() => _status = 'Saving finishing data...');\r\n"
    b"        final finishing = _finishingResult!['finishing'];\r\n"
    b"        await api.postFinishing(\r\n"
    b"          widget.projectId,\r\n"
    b"          finishing is Map<String, dynamic> ? finishing : _finishingResult!,\r\n"
    b"        );\r\n"
    b"      }\r\n"
    b"\r\n"
    b"      await api.postBuildingStructure(\r\n"
    b"          widget.projectId, _wallingResult ?? <String, dynamic>{});\r\n"
    b"\r\n"
    b"      // Background: generate 3D views - non-fatal\r\n"
    b"      _generate3dInBackground(api);\r\n"
    b"\r\n"
    b"      if (!mounted) return;\r\n"
    b"      setState(() {\r\n"
    b"        _pipelineStep = 6;\r\n"
    b"        _loading = false;\r\n"
    b"        _status = '';\r\n"
    b"      });\r\n"
    b"    } catch (e) {"
)

if old in data:
    data = data.replace(old, new_block, 1)
    with open('lib/screens/upload_building_plan_screen.dart', 'wb') as f:
        f.write(data)
    print('OK: replacement done')
else:
    # Try to find what's actually there
    idx1 = data.find(b'postBuildingStructure')
    idx2 = data.rfind(b'_pipelineStep = 4')
    print(f'NOT FOUND. postBuildingStructure at {idx1}, _pipelineStep=4 at {idx2}')
    if idx2 > 0:
        print(repr(data[max(0,idx2-400):idx2+50]))
    sys.exit(1)
