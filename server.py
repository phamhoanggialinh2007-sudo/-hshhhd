import os
import re
import random
import string
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Cho phép CORS cho frontend từ domain khác

def check_syntax(code):
    """Kiểm tra cú pháp LuaU chuẩn: nested blocks, dấu ngoặc, string, multi-line string, comment"""
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    keyword_stack = []

    # Các từ khóa mở và đóng
    open_keywords = {'if', 'for', 'while', 'function', 'repeat'}
    close_map = {'if': 'end', 'for': 'end', 'while': 'end', 'function': 'end', 'repeat': 'until'}

    in_string = False
    string_type = None
    in_longstring = False
    in_comment = False

    lines = code.split('\n')
    for line in lines:
        i = 0
        while i < len(line):
            c = line[i]

            # Multi-line comment
            if not in_string and not in_longstring and line[i:i+4] == '--[[':
                in_longstring = True
                i += 4
                continue
            if in_longstring and line[i:i+2] == ']]':
                in_longstring = False
                i += 2
                continue

            # Single-line comment
            if not in_string and not in_longstring and line[i:i+2] == '--':
                break  # Bỏ qua phần còn lại của line

            # Multi-line string
            if not in_string and not in_longstring and line[i:i+2] == '[[':
                in_longstring = True
                i += 2
                continue
            if in_longstring and line[i:i+2] == ']]':
                in_longstring = False
                i += 2
                continue

            # String
            if not in_string and c in ('"', "'"):
                in_string = True
                string_type = c
                i += 1
                continue
            if in_string:
                if c == string_type and (i == 0 or line[i-1] != '\\'):
                    in_string = False
                i += 1
                continue

            # Brackets
            if c in brackets:
                stack.append(c)
            elif c in brackets.values():
                if not stack or brackets[stack.pop()] != c:
                    return False

            # Token check
            if c.isalpha():
                token = ''
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    token += line[i]
                    i += 1
                if token in open_keywords:
                    keyword_stack.append(token)
                elif token in ('end', 'until'):
                    if not keyword_stack:
                        return False
                    expected = close_map[keyword_stack[-1]]
                    if token != expected:
                        return False
                    keyword_stack.pop()
                continue
            i += 1

    return not stack and not keyword_stack and not in_string and not in_longstring

# ------------------- Obfuscate logic giữ nguyên -------------------

def obfuscate(code):
    """Obfuscation LuaU cực mạnh: 4 lớp XOR, junk code thông minh, control flow rối, anti-tamper an toàn."""
    code = re.sub(r'--.*|(--\[\[.*?\]\])', '', code, flags=re.DOTALL)
    code = re.sub(r'\s+', ' ', code).strip()

    keywords = set(['and','break','do','else','elseif','end','false','for','function','goto','if','in','local','nil','not','or','repeat','return','then','true','until','while'])
    identifiers = set(re.findall(r'\b[a-zA-Z_]\w*\b', code))
    vars_to_rename = identifiers - keywords
    rename_map = {v: '_0x' + hex(random.randint(0, 0xFFFFF))[2:].zfill(5) for v in vars_to_rename}
    for old, new in rename_map.items():
        code = re.sub(r'\b' + re.escape(old) + r'\b', new, code)

    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    def base64_encode(data):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')

    def encode_string(match):
        str_content = match.group(1)
        keys = [random.randint(1, 255) for _ in range(4)]
        encoded = str_content
        for key in keys:
            encoded = ''.join(chr(ord(c) ^ key) for c in encoded)
        encoded_b64 = base64_encode(encoded)
        decoder = f'''(function(_b64, _k1,_k2,_k3,_k4)
local _chars="{base64_chars}" local _result={{}} local _i=1 local _bits=0 local _count=0 local _val=0
for _c=1,#_b64 do local _char=_b64:sub(_c,_c) if _char=="=" then break end local _idx=_chars:find(_char)-1
if _idx>=0 then _val=_val*64+_idx _count=_count+1
if _count==4 then _result[_i]=string.char(bit32.bxor(bit32.rshift(_val,16)%256,_k4))
_result[_i+1]=string.char(bit32.bxor(bit32.rshift(_val,8)%256,_k4))
_result[_i+2]=string.char(bit32.bxor(_val%256,_k4)) _i=_i+3 _val=0 _count=0 end end end
if _count==3 then _result[_i]=string.char(bit32.bxor(bit32.rshift(_val,10)%256,_k4)) _result[_i+1]=string.char(bit32.bxor(bit32.rshift(_val,2)%256,_k4))
elseif _count==2 then _result[_i]=string.char(bit32.bxor(bit32.rshift(_val,4)%256,_k4)) end
local _dec=table.concat(_result) for _l=2,4 do local _tmp='' for _j=1,#_dec do _tmp=_tmp..string.char(bit32.bxor(_dec:byte(_j),(_l==2 and _k3 or _l==3 and _k2 or _k1))) end _dec=_tmp end return _dec end)("{encoded_b64}",{keys[0]},{keys[1]},{keys[2]},{keys[3]})'''
        return decoder

    code = re.sub(r'"(.*?)"', encode_string, code)
    code = re.sub(r"'(.*?)'", encode_string, code)

    junk_snippets = [
        f'local _0x{random.randint(1000,9999)}=math.random(1,1000);if _0x{random.randint(1000,9999)}>9999 then warn("fake") end;',
        f'function _fake{random.randint(1000,9999)}() return math.random()*0 end; _fake{random.randint(1000,9999)}=nil;',
        f'repeat local _j{random.randint(1000,9999)}=1 until _j{random.randint(1000,9999)}>0;',
        f'local _trap{random.randint(1000,9999)}=math.random()*0 if _trap{random.randint(1000,9999)}~=0 then warn("trap") end;',
        f'if math.random()>1 then error("trap{random.randint(1000,9999)}") end;',
    ]
    parts = code.split(';')
    for i in range(len(parts)-1,0,-1):
        if random.random()<0.35:
            parts.insert(i, random.choice(junk_snippets))
    code=';'.join(parts)

    code = re.sub(r'if\s+(\w+)\s*>\s*(\d+)\s*then', r'if math.floor(math.tan(\1/\2)*1000)%2==1 then', code)
    code = re.sub(r'if\s+(\w+)\s*==\s*(\d+)\s*then', r'if math.abs(\1-\2)<0.0001 then', code)
    fake_label=f'_lbl{random.randint(1000,9999)}'
    code=f'goto {fake_label};if math.random()>1 then error("fake") end;::{fake_label}::'+code+';repeat until math.random()>-1'

    anti_tamper='''
local _env=getfenv() local _start=tick() wait(0.001)
if tick()-_start>0.005 then warn("Possible tamper detected") end
if _env.debug or type(_G)~="table" then warn("Environment modified") end
local _trap=math.random()*0 if _trap~=0 then warn("Trap triggered") end
'''
    code=anti_tamper+code

    split_parts=[code[i:i+70] for i in range(0,len(code),70)]
    key_split=random.randint(1,255)
    encoded_parts=[''.join(chr(ord(c)^key_split) for c in part) for part in split_parts]
    reassemble='..'.join(f'''(function(_s,_k)local _r='' for _i=1,#_s do _r=_r..string.char(bit32.bxor(_s:byte(_i),_k)) end return _r end)("{ep}",{key_split})''' for ep in encoded_parts)
    code=f'loadstring({reassemble})()'

    keys_outer=[random.randint(1,255) for _ in range(4)]
    encoded=code
    for key in keys_outer:
        encoded=''.join(chr(ord(c)^key) for c in encoded)
    multi_decoder=f'''
local function _multi_dec(_s,_k1,_k2,_k3,_k4)
local _r=_s
for _l=1,4 do
local _tmp=''
for _i=1,#_r do _tmp=_tmp..string.char(bit32.bxor(_r:byte(_i),(_l==1 and _k4 or _l==2 and _k3 or _l==3 and _k2 or _k1))) end
_r=_tmp
end
return _r
end
loadstring(_multi_dec("{encoded}",{keys_outer[0]},{keys_outer[1]},{keys_outer[2]},{keys_outer[3]}))()
'''
    return multi_decoder

# ------------------- Flask API -------------------

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code=request.form.get('code','')
    file=request.files.get('file')
    if file and file.filename:
        input_code=file.read().decode('utf-8')

    if not input_code.strip():
        return jsonify({'error':'Vui lòng nhập hoặc upload code LuaU!'}),400

    if not check_syntax(input_code):
        return jsonify({'error':'Lỗi cú pháp trong code LuaU!'}),400

    obfuscated=obfuscate(input_code)
    if not check_syntax(obfuscated):
        return jsonify({'error':'Lỗi cú pháp sau mã hóa, thử lại!'}),500

    return jsonify({'output':obfuscated,'status':'Mã hóa thành công! Code LuaU siêu an toàn.'})

if __name__=='__main__':
    port=int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port,debug=False)
