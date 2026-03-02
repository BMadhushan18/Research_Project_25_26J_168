import sys

def find_unmatched(path):
    s=open(path,'r',encoding='utf-8').read()
    stack=[]
    for i,ch in enumerate(s):
        if ch=='(':
            stack.append(i)
        elif ch==')':
            if stack:
                stack.pop()
            else:
                line = s.count('\n', 0, i) + 1
                col = i - s.rfind('\n', 0, i)
                print(path, 'extra ) at', i, 'line', line, 'col', col)
                return
    if stack:
        idx=stack[-1]
        # compute line/column
        line = s.count('\n', 0, idx) + 1
        col = idx - s.rfind('\n', 0, idx)
        start = max(0, idx-40)
        end = min(len(s), idx+40)
        context = s[start:end]
        print(path, 'unmatched ( at', idx, 'line', line, 'col', col)
        print('Context:\n', context)
    else:
        print(path, 'balanced')

if __name__=='__main__':
    find_unmatched('c:/research clone 2/Research_Project_25_26J_168/flutterApp/lib/screens/home_page.dart')
    find_unmatched('c:/research clone 2/Research_Project_25_26J_168/flutterApp/lib/screens/material_detail_screen.dart')
