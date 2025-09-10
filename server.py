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
    in_line_comment = False

    lines = code.split('\n')
    for line_num, line in enumerate(lines):
        i = 0
        in_line_comment = False
        
        while i < len(line):
            c = line[i]

            # Multi-line comment
            if not in_string and not in_longstring and not in_line_comment and line[i:i+4] == '--[[':
                in_longstring = True
                i += 4
                continue
            if in_longstring and line[i:i+2] == ']]':
                in_longstring = False
                i += 2
                continue

            # Single-line comment
            if not in_string and not in_longstring and line[i:i+2] == '--' and not in_line_comment:
                in_line_comment = True
                i += 2
                continue
            if in_line_comment:
                i += 1
                continue

            # Multi-line string
            if not in_string and not in_longstring and not in_line_comment and line[i:i+2] == '[[':
                in_longstring = True
                i += 2
                continue
            if in_longstring and line[i:i+2] == ']]':
                in_longstring = False
                i += 2
                continue

            # String
            if not in_string and not in_longstring and not in_line_comment and c in ('"', "'"):
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
            if not in_string and not in_longstring and not in_line_comment:
                if c in brackets:
                    stack.append((c, line_num))
                elif c in brackets.values():
                    if not stack:
                        return False, f"Unmatched closing bracket '{c}' at line {line_num+1}"
                    last_open, open_line = stack.pop()
                    if brackets[last_open] != c:
                        return False, f"Mismatched brackets: '{last_open}' at line {open_line+1} and '{c}' at line {line_num+1}"

            # Token check
            if not in_string and not in_longstring and not in_line_comment and c.isalpha():
                token = ''
                start_i = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    token += line[i]
                    i += 1
                
                if token in open_keywords:
                    keyword_stack.append((token, line_num))
                elif token in ('end', 'until'):
                    if not keyword_stack:
                        return False, f"Unmatched '{token}' at line {line_num+1}"
                    last_keyword, keyword_line = keyword_stack[-1]
                    expected = close_map.get(last_keyword)
                    if token != expected:
                        return False, f"Mismatched block: '{last_keyword}' at line {keyword_line+1} and '{token}' at line {line_num+1}"
                    keyword_stack.pop()
                continue
            i += 1

    if stack:
        last_bracket, line_num = stack[-1]
        return False, f"Unclosed bracket '{last_bracket}' at line {line_num+1}"
    
    if keyword_stack:
        last_keyword, line_num = keyword_stack[-1]
        return False, f"Unclosed block '{last_keyword}' at line {line_num+1}"
    
    if in_string:
        return False, "Unclosed string literal"
    
    if in_longstring:
        return False, "Unclosed long string or comment"
    
    return True, "Syntax is valid"

# ------------------- Obfuscate logic nâng cấp -------------------

def obfuscate(code):
    """Obfuscation LuaU cực mạnh: 4 lớp XOR, junk code thông minh, control flow rối, anti-tamper an toàn."""
    # Loại bỏ comment nhưng giữ nguyên string và các phần quan trọng
    code = re.sub(r'--\[\[.*?\]\]', '', code, flags=re.DOTALL)  # Multi-line comments
    code = re.sub(r'--[^\n]*', '', code)  # Single-line comments
    
    # Chuẩn hóa khoảng trắng
    code = re.sub(r'\s+', ' ', code).strip()

    # Tìm và đổi tên các biến
    keywords = set(['and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 
                   'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then', 
                   'true', 'until', 'while'])
    
    # Tìm tất cả các định danh
    identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    vars_to_rename = identifiers - keywords
    
    # Tạo bản đồ đổi tên với định dạng hex ngẫu nhiên
    rename_map = {}
    for var in vars_to_rename:
        # Tạo tên mới với định dạng phức tạp hơn
        new_name = '_0x' + ''.join(random.choices('0123456789abcdef', k=8)) + '_' + ''.join(random.choices('ABCDEF', k=4))
        rename_map[var] = new_name
    
    # Đổi tên các biến, tránh thay thế trong string
    tokens = re.split(r'(".*?"|\'.*?\'|\[\[.*?\]\])', code)
    for i in range(len(tokens)):
        if i % 2 == 0:  # Không phải string
            for old, new in rename_map.items():
                tokens[i] = re.sub(r'\b' + re.escape(old) + r'\b', new, tokens[i])
    
    code = ''.join(tokens)

    # Mã hóa string với XOR nhiều lớp
    base64_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    def base64_encode(data):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    
    def encode_string(match):
        str_content = match.group(1)
        # Tạo 4 khóa ngẫu nhiên
        keys = [random.randint(1, 255) for _ in range(4)]
        
        # Mã hóa nhiều lớp
        encoded = str_content
        for key in keys:
            encoded = ''.join(chr(ord(c) ^ key) for c in encoded)
        
        encoded_b64 = base64_encode(encoded)
        
        # Tạo decoder phức tạp
        decoder = f'''(function()
    local _b64 = "{encoded_b64}"
    local _k1, _k2, _k3, _k4 = {keys[0]}, {keys[1]}, {keys[2]}, {keys[3]}
    local _chars = "{base64_chars}"
    local _result = {{}}
    local _i = 1
    local _bits = 0
    local _count = 0
    local _val = 0
    
    for _c = 1, #_b64 do
        local _char = _b64:sub(_c, _c)
        if _char == "=" then break end
        local _idx = _chars:find(_char) - 1
        if _idx >= 0 then
            _val = _val * 64 + _idx
            _count = _count + 1
            if _count == 4 then
                _result[_i] = string.char(bit32.bxor(bit32.rshift(_val, 16) % 256, _k4))
                _result[_i+1] = string.char(bit32.bxor(bit32.rshift(_val, 8) % 256, _k4))
                _result[_i+2] = string.char(bit32.bxor(_val % 256, _k4))
                _i = _i + 3
                _val = 0
                _count = 0
            end
        end
    end
    
    if _count == 3 then
        _result[_i] = string.char(bit32.bxor(bit32.rshift(_val, 10) % 256, _k4))
        _result[_i+1] = string.char(bit32.bxor(bit32.rshift(_val, 2) % 256, _k4))
    elseif _count == 2 then
        _result[_i] = string.char(bit32.bxor(bit32.rshift(_val, 4) % 256, _k4))
    end
    
    local _dec = table.concat(_result)
    
    -- Giải mã nhiều lớp
    for _l = 1, 3 do
        local _tmp = ""
        for _j = 1, #_dec do
            local _byte = _dec:byte(_j)
            if _l == 1 then
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k3))
            elseif _l == 2 then
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k2))
            else
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k1))
            end
        end
        _dec = _tmp
    end
    
    return _dec
end)()'''
        return decoder

    # Mã hóa tất cả các string
    tokens = re.split(r'(".*?"|\'.*?\'|\[\[.*?\]\])', code)
    for i in range(len(tokens)):
        if i % 2 == 1:  # Phần string
            if tokens[i].startswith('"') and tokens[i].endswith('"'):
                tokens[i] = encode_string(re.match(r'"(.*)"', tokens[i]))
            elif tokens[i].startswith("'") and tokens[i].endswith("'"):
                tokens[i] = encode_string(re.match(r"'(.*)'", tokens[i]))
    
    code = ''.join(tokens)

    # Thêm junk code thông minh
    junk_snippets = [
        f'local _0x{random.randint(10000,99999)} = math.random(1, 1000); if _0x{random.randint(10000,99999)} > 9999 then warn("fake") end;',
        f'function _fake{random.randint(10000,99999)}() return math.random() * 0 end; _fake{random.randint(10000,99999)} = nil;',
        f'repeat local _j{random.randint(10000,99999)} = 1 until _j{random.randint(10000,99999)} > 0;',
        f'local _trap{random.randint(10000,99999)} = math.random() * 0; if _trap{random.randint(10000,99999)} ~= 0 then warn("trap") end;',
        f'if math.random() > 1 then error("trap{random.randint(10000,99999)}") end;',
        f'for _i{random.randint(10000,99999)} = 1, math.random(1, 3) do local _tmp{random.randint(10000,99999)} = _i{random.randint(10000,99999)} * 0 end;',
        f'local _arr{random.randint(10000,99999)} = {{}}; for _k{random.randint(10000,99999)} = 1, math.random(2, 5) do table.insert(_arr{random.randint(10000,99999)}, _k{random.randint(10000,99999)}) end;',
    ]
    
    # Chèn junk code một cách thông minh
    lines = code.split(';')
    new_lines = []
    
    for line in lines:
        new_lines.append(line)
        if random.random() < 0.4 and line.strip():  # 40% chance to add junk after non-empty lines
            new_lines.append(random.choice(junk_snippets))
    
    code = ';'.join(new_lines)

    # Làm rối control flow
    code = re.sub(r'if\s+([^\s]+)\s*>\s*(\d+)\s*then', 
                 r'if math.floor(math.tan(\1/\2)*1000)%2==1 then', code)
    code = re.sub(r'if\s+([^\s]+)\s*==\s*(\d+)\s*then', 
                 r'if math.abs(\1-\2)<0.0001 then', code)
    
    # Thêm control flow giả
    fake_label = f'_lbl{random.randint(10000,99999)}'
    code = f'goto {fake_label}; if math.random() > 1 then error("fake") end; ::{fake_label}:: ' + code
    
    # Thêm anti-tamper protection
    anti_tamper = f'''
local _env = getfenv()
local _start = tick()
wait(0.001)
if tick() - _start > 0.005 then
    warn("Possible tamper detected")
end
if _env.debug or type(_G) ~= "table" then
    warn("Environment modified")
end
local _trap{random.randint(10000,99999)} = math.random() * 0
if _trap{random.randint(10000,99999)} ~= 0 then
    warn("Trap triggered")
end
'''
    code = anti_tamper + code

    # Mã hóa toàn bộ code thành các phần
    split_parts = [code[i:i+70] for i in range(0, len(code), 70)]
    key_split = random.randint(1, 255)
    encoded_parts = [''.join(chr(ord(c) ^ key_split) for c in part) for part in split_parts]
    
    reassemble = ' .. '.join([
        f'''(function(_s, _k)
    local _r = ''
    for _i = 1, #_s do
        _r = _r .. string.char(bit32.bxor(_s:byte(_i), _k))
    end
    return _r
end)("{ep}", {key_split})''' for ep in encoded_parts
    ])
    
    code = f'loadstring({reassemble})()'

    # Mã hóa lớp cuối cùng với XOR nhiều lớp
    keys_outer = [random.randint(1, 255) for _ in range(4)]
    encoded = code
    for key in keys_outer:
        encoded = ''.join(chr(ord(c) ^ key) for c in encoded)
    
    # Tạo multi-layer decoder
    multi_decoder = f'''
local function _multi_dec(_s, _k1, _k2, _k3, _k4)
    local _r = _s
    for _l = 1, 4 do
        local _tmp = ''
        for _i = 1, #_r do
            local _byte = _r:byte(_i)
            if _l == 1 then
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k4))
            elseif _l == 2 then
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k3))
            elseif _l == 3 then
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k2))
            else
                _tmp = _tmp .. string.char(bit32.bxor(_byte, _k1))
            end
        end
        _r = _tmp
    end
    return _r
end

local _encrypted_code = "{encoded}"
local _decrypted_code = _multi_dec(_encrypted_code, {keys_outer[0]}, {keys_outer[1]}, {keys_outer[2]}, {keys_outer[3]})
loadstring(_decrypted_code)()
'''
    
    return multi_decoder

# ------------------- Flask API -------------------

@app.route('/api/obfuscate', methods=['POST'])
def api_obfuscate():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file and file.filename:
        try:
            input_code = file.read().decode('utf-8')
        except Exception as e:
            return jsonify({'error': f'Lỗi đọc file: {str(e)}'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Vui lòng nhập hoặc upload code LuaU!'}), 400

    # Kiểm tra cú pháp
    is_valid, message = check_syntax(input_code)
    if not is_valid:
        return jsonify({'error': f'Lỗi cú pháp: {message}'}), 400

    try:
        obfuscated = obfuscate(input_code)
        # Kiểm tra lại cú pháp sau khi obfuscate
        is_valid, message = check_syntax(obfuscated)
        if not is_valid:
            return jsonify({'error': f'Lỗi cú pháp sau mã hóa: {message}'}), 500
            
        return jsonify({
            'output': obfuscated,
            'status': 'Mã hóa thành công! Code LuaU siêu an toàn.'
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi trong quá trình mã hóa: {str(e)}'}), 500

@app.route('/api/check_syntax', methods=['POST'])
def api_check_syntax():
    input_code = request.form.get('code', '')
    file = request.files.get('file')
    
    if file and file.filename:
        try:
            input_code = file.read().decode('utf-8')
        except Exception as e:
            return jsonify({'error': f'Lỗi đọc file: {str(e)}'}), 400

    if not input_code.strip():
        return jsonify({'error': 'Vui lòng nhập hoặc upload code LuaU!'}), 400

    is_valid, message = check_syntax(input_code)
    
    return jsonify({
        'valid': is_valid,
        'message': message
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
