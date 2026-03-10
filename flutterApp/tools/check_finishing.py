with open('lib/screens/upload_building_plan_screen.dart','r',encoding='utf-8',errors='replace') as f: d=f.read()

# Show SF nextLabel
idx=d.find('Continue - Finishing')
print('SF nextLabel context:', repr(d[max(0,idx-30):idx+60]))

# State vars
state_start=d.find('int _pipelineStep')
print('state vars:')
print(d[state_start:state_start+350])

# pipeline progress
prog=d.find('const steps = [')
print('progress:', repr(d[prog:prog+200]))

# _pipelineStep = 4 occurrence context in saveAndComplete
idx4=d.find('_pipelineStep = 4')
print('step4 set:', repr(d[max(0,idx4-40):idx4+80]))
