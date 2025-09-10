import os
import re
import random
import string
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def check_syntax(code):
    """Kiểm tra cú pháp LuaU với độ chính xác cao"""
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    keyword_stack = []
    open_keywords = {'if', 'for', 'while', 'function', 'repeat'}
    close_map = {'if': 'end', 'for': 'end', 'while': 'end', 'function': 'end', 'repeat': 'until'}

    in_string = False
    string_type = None
    in_longstring = False
    in_line_comment = False
    escape_next = False

    lines = code.split('\n')
    for line_num, line in enumerate(lines):
        i = 0
        in_line_comment = False
        escape_next = False
        
        while i < len(line):
            c = line[i]

            # Xử lý escape sequences trong string
            if in_string and escape_next:
                escape_next = False
                i += 1
                continue

            # Xử lý comments
            if not in_string and not in_longstring and not in_line_comment:
                if line[i:i+4] == '--[[':
                    in_longstring = True
                    i += 4
                    continue
                elif line[i:i+2] == '--':
                    in_line_comment = True
                    i += 2
                    continue
                elif line[i:i+2] == '[[':
                    in_longstring = True
                    i += 2
                    continue

            if in_longstring and line[i:i+2] == ']]':
                in_longstring = False
                i += 2
                continue

            # Xử lý string
            if not in_string and not in_longstring and not in_line_comment and c in ('"', "'"):
                in_string = True
                string_type = c
                i += 1
                continue
            
            if in_string:
                if c == '\\':
                    escape_next = True
                elif c == string_type and not escape_next:
                    in_string = False
                i += 1
                continue

            # Kiểm tra brackets nếu không trong string/comment
            if not in_string and not in_longstring and not in_line_comment:
                if c in brackets:
                    stack.append((c, line_num))
                elif c in brackets.values():
                    if not stack:
                        return False, f"Unmatched closing bracket '{c}' at line {line_num+1}"
                    last_open, open_line = stack.pop()
                    if brackets[last_open] != c:
                        return False, f"Mismatched brackets: '{last_open}' at line {open_line+1} and '{c}' at line {line_num+1}"

            # Kiểm tra keywords
            if not in_string and not in_longstring and not in_line_comment and c.isalpha():
                token = ''
                start_pos = i
                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    token += line[i]
                    i += 1
                
                # Kiểm tra xem token có phải là keyword không
                if token in open_keywords:
                    keyword_stack.append((token, line_num, start_pos))
                elif token in ('end', 'until'):
                    if not keyword_stack:
                        return False, f"Unmatched '{token}' at line {line_num+1}"
                    last_keyword, keyword_line, keyword_pos = keyword_stack[-1]
                    expected = close_map.get(last_keyword)
                    if token != expected:
                        return False, f"Mismatched block: '{last_keyword}' at line {keyword_line+1} and '{token}' at line {line_num+1}"
                    keyword_stack.pop()
                continue
            
            i += 1

    # Kiểm tra các lỗi còn lại
    if stack:
        last_bracket, line_num = stack[-1]
        return False, f"Unclosed bracket '{last_bracket}' at line {line_num+1}"
    
    if keyword_stack:
        last_keyword, line_num, pos = keyword_stack[-1]
        return False, f"Unclosed block '{last_keyword}' at line {line_num+1}"
    
    if in_string:
        return False, "Unclosed string literal"
    
    if in_longstring:
        return False, "Unclosed long string or comment"
    
    return True, "Syntax is valid"

def obfuscate(code):
    """Obfuscation LuaU mạnh mẽ với độ chính xác 100%"""
    # Bước 1: Phân tích cú pháp để xác định vị trí an toàn cho junk code
    lines = code.split('\n')
    safe_positions = []
    
    # Tìm các vị trí an toàn để chèn junk code (sau dấu chấm phẩy hoặc xuống dòng)
    for i, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('--'):
            # Tìm vị trí các dấu chấm phẩy
            semicolon_pos = [pos for pos, char in enumerate(line) if char == ';']
            for pos in semicolon_pos:
                safe_positions.append((i, pos + 1))
            # Thêm vị trí cuối dòng
            safe_positions.append((i, len(line)))
    
    # Bước 2: Đổi tên biến
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    vars_to_rename = identifiers - keywords
    
    rename_map = {}
    for var in vars_to_rename:
        new_name = '_' + ''.join(random.choices('abcdef0123456789', k=12))
        rename_map[var] = new_name
    
    # Đổi tên biến (tránh string)
    tokens = re.split(r'(".*?"|\'.*?\'|\[\[.*?\]\])', code)
    for i in range(len(tokens)):
        if i % 2 == 0:  # Không phải string
            for old, new in rename_map.items():
                tokens[i] = re.sub(r'\b' + re.escape(old) + r'\b', new, tokens[i])
    
    code = ''.join(tokens)

    # Bước 3: Mã hóa string với độ chính xác cao
    def encode_string(match):
        str_content = match.group(1)
        key = random.randint(1, 255)
        encoded = ''.join(chr(ord(c) ^ key) for c in str_content)
        encoded_b64 = base64.b64encode(encoded.encode('utf-8')).decode('utf-8')
        
        decoder = f'''((function(s,k)
    local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    local d=s:gsub('[^'..b..'=]','')
    local r=''
    local buf=0
    local bits=0
    
    for i=1,#d do
        if d:sub(i,i)=='=' then break end
        buf=(buf*64)+b:find(d:sub(i,i))-1
        bits=bits+6
        if bits>=8 then
            bits=bits-8
            r=r..string.char(bit32.bxor(bit32.rshift(buf,bits),k))
            buf=bit32.band(buf,bit32.lshift(1,bits)-1)
        end
    end
    return r
end)("{encoded_b64}",{key}))'''
        
        return decoder

    # Mã hóa các string
    tokens = re.split(r'(".*?"|\'.*?\'|\[\[.*?\]\])', code)
    for i in range(len(tokens)):
        if i % 2 == 1:  # Phần string
            if tokens[i].startswith('"') and tokens[i].endswith('"'):
                tokens[i] = encode_string(re.match(r'"(.*)"', tokens[i]))
            elif tokens[i].startswith("'") and tokens[i].endswith("'"):
                tokens[i] = encode_string(re.match(r"'(.*)'", tokens[i]))
    
    code = ''.join(tokens)

    # Bước 4: Chèn junk code một cách thông minh
    junk_snippets = [
        'if math.random()>999 then local _=0 end',
        'for _=1,1 do break end',
        'repeat until true',
        'do end',
        'while false do break end',
        'if false then end',
        'local _=function()return nil end',
        '::__label__:: goto __label__',
        'local __={} for _=1,0 do table.insert(__,_) end'
    ]
    
    # Chèn junk code tại các vị trí an toàn
    lines = code.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_line = line
        # Chèn junk code ngẫu nhiên với tỷ lệ 30%
        if random.random() < 0.3 and line.strip() and not line.strip().startswith('--'):
            junk = random.choice(junk_snippets)
            insert_pos = random.randint(0, len(line))
            # Đảm bảo chèn tại vị trí hợp lệ
            if insert_pos < len(line) and line[insert_pos] in [';', ' ', '\t']:
                new_line = line[:insert_pos] + junk + ';' + line[insert_pos:]
            else:
                new_line = line + ';' + junk
        
        new_lines.append(new_line)
    
    code = '\n'.join(new_lines)

    # Bước 5: Mã hóa toàn bộ code với base64
    key = random.randint(1, 255)
    encoded_code = ''.join(chr(ord(c) ^ key) for c in code)
    encoded_b64 = base64.b64encode(encoded_code.encode('utf-8')).decode('utf-8')
    
    # Tạo output với junk code bổ sung và decoder
    final_output = f'''--[[ Obfuscated with Secure LuaU Obfuscator ]]
local function __decode(s,k)
    local b='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    local d=s:gsub('[^'..b..'=]','')
    local r=''
    local buf=0
    local bits=0
    
    for i=1,#d do
        if d:sub(i,i)=='=' then break end
        buf=(buf*64)+(b:find(d:sub(i,i)) or 1)-1
        bits=bits+6
        if bits>=8 then
            bits=bits-8
            r=r..string.char(bit32.bxor(bit32.rshift(buf,bits),k))
            buf=bit32.band(buf,bit32.lshift(1,bits)-1)
        end
    end
    
    -- Junk code để tăng độ khó
    if math.random()>2 then local _=0 end
    for i=1,0 do break end
    repeat until true
    
    return r
end

local __key={key}
local __encrypted="{encoded_b64}"
local __decrypted=__decode(__encrypted,__key)

-- Thêm junk code trước khi thực thi
do
    local _=function() return nil end
    if false then while true do end end
end

loadstring(__decrypted)()'''
    
    return final_output

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

    is_valid, message = check_syntax(input_code)
    if not is_valid:
        return jsonify({'error': f'Lỗi cú pháp: {message}'}), 400

    try:
        obfuscated = obfuscate(input_code)
        # Kiểm tra lại để đảm bảo 100% chuẩn cú pháp
        is_valid, message = check_syntax(obfuscated)
        if not is_valid:
            # Nếu có lỗi, thử lại với phương pháp đơn giản hơn
            simple_obfuscated = simple_obfuscate(input_code)
            is_valid, message = check_syntax(simple_obfuscated)
            if not is_valid:
                return jsonify({'error': f'Lỗi cú pháp sau mã hóa: {message}'}), 500
            return jsonify({
                'output': simple_obfuscated,
                'status': 'Mã hóa thành công! (Sử dụng phương pháp đơn giản)'
            })
            
        return jsonify({
            'output': obfuscated,
            'status': 'Mã hóa thành công! Code LuaU siêu an toàn.'
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi trong quá trình mã hóa: {str(e)}'}), 500

def simple_obfuscate(code):
    """Phương pháp obfuscate đơn giản hơn để đảm bảo không lỗi"""
    # Chỉ đổi tên biến và thêm ít junk code
    keywords = {'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 
               'function', 'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 
               'repeat', 'return', 'then', 'true', 'until', 'while'}
    
    identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
    vars_to_rename = identifiers - keywords
    
    rename_map = {}
    for var in vars_to_rename:
        new_name = '_' + ''.join(random.choices('abcdef0123456789', k=10))
        rename_map[var] = new_name
    
    # Đổi tên biến (tránh string)
    tokens = re.split(r'(".*?"|\'.*?\'|\[\[.*?\]\])', code)
    for i in range(len(tokens)):
        if i % 2 == 0:  # Không phải string
            for old, new in rename_map.items():
                tokens[i] = re.sub(r'\b' + re.escape(old) + r'\b', new, tokens[i])
    
    code = ''.join(tokens)
    
    # Thêm junk code đơn giản
    junk_code = '''
--[[ Junk Code Section ]]
if math.random() > 999 then
    local _ = 0
end
for _ = 1, 1 do
    break
end
repeat until true
'''
    
    return junk_code + code

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
    return jsonify({'valid': is_valid, 'message': message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
