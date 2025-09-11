import random
import string
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from io import BytesIO
import math

app = Flask(__name__)
CORS(app)  # Cho phép truy cập từ các domain khác

def generate_random_name(length=2):
    """Tạo tên ngẫu nhiên với độ dài chỉ định - tối ưu cho Luau"""
    first_char = random.choice(string.ascii_letters + '_')
    rest_chars = ''.join(random.choice(string.ascii_letters + string.digits + '_') for _ in range(length-1))
    return first_char + rest_chars

def multi_layer_xor(data, layers=2):
    """Mã hóa nhiều lớp XOR với các key ngẫu nhiên - tối ưu hóa"""
    encrypted_data = data.encode('utf-8')
    keys = []
    
    for _ in range(layers):
        key_len = random.randint(3, 8)
        key = bytes([random.randint(1, 255) for _ in range(key_len)])
        encrypted_data = bytes([b ^ key[i % key_len] for i, b in enumerate(encrypted_data)])
        keys.append(key)
    
    return encrypted_data, keys

def generate_luau_junk_statements(count=5):
    """Tạo các câu lệnh rác ngẫu nhiên tương thích với Luau"""
    junk_templates = [
        "if {0} then local {1}={2} end",
        "for {1}={2},{3} do local {4}={5} end",
        "while {0} do break end",
        "repeat until {0}",
        "local {1}={2}",
        "local function {1}(...) return {2} end",
        "{1}={2}",
        "do local {1}={2} end",
        "local {1} = function() return {2} end",
        "if not {0} then else end",
        "::{1}::",
        "goto {1}",
        "local {1} = {{{2}}}",
        "local {1} = setmetatable({{}}, {{}})",
        "local {1} = typeof({2})",
        "task.spawn(function() {2} end)",
        "local {1} = Instance.new('Part')",
        "local {1} = game:GetService('{2}')"
    ]
    
    junk_statements = []
    for _ in range(count):
        template = random.choice(junk_templates)
        vars_needed = template.count('{')
        vars_list = [generate_random_name() for _ in range(vars_needed)]
        
        # Tạo giá trị ngẫu nhiên tương thích với Luau
        values = []
        for i in range(vars_needed):
            if i % 4 == 0:
                values.append(random.choice(['true', 'false', 'nil']))
            elif i % 4 == 1:
                values.append(str(random.randint(1, 100)))
            elif i % 4 == 2:
                values.append(f'"{generate_random_name(4)}"')
            else:
                values.append("{}")
        
        try:
            junk_statements.append(template.format(*values))
        except:
            # Nếu có lỗi định dạng, bỏ qua câu lệnh này
            continue
    
    return junk_statements

def obfuscate_luau_names(code):
    """Đổi tên biến và hàm thành tên ngẫu nhiên - tối ưu cho Luau"""
    # Tìm tất cả các biến và hàm không phải từ khóa
    reserved_words = {
        'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 
        'goto', 'if', 'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 
        'then', 'true', 'until', 'while', 'continue', 'typeof', 'task', 'self'
    }
    
    # Tìm tất cả các định danh
    pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'
    identifiers = re.findall(pattern, code)
    
    # Lọc ra các từ khóa và chỉ lấy các định danh có thể đổi tên
    identifiers = [id for id in set(identifiers) if id not in reserved_words and not id.isdigit() and len(id) > 1]
    
    # Tạo ánh xạ tên mới
    mapping = {}
    for identifier in identifiers:
        # Giữ nguyên các phương thức đối tượng (dạng obj:method)
        if ':' in identifier:
            continue
            
        # Giữ nguyên các biến toàn cục (không có local)
        if not re.search(r'\blocal\s+' + re.escape(identifier), code):
            continue
            
        if identifier not in mapping:
            mapping[identifier] = generate_random_name()
    
    # Thay thế tên
    for old_name, new_name in mapping.items():
        code = re.sub(r'\b' + re.escape(old_name) + r'\b', new_name, code)
    
    return code, mapping

def flatten_luau_code(code):
    """Làm phẳng mã Luau: xóa comment, khoảng trắng thừa, xuống dòng"""
    # Xóa comment một dòng
    code = re.sub(r'--.*$', '', code, flags=re.MULTILINE)
    
    # Xóa comment nhiều dòng
    code = re.sub(r'--\[\[.*?\]\]', '', code, flags=re.DOTALL)
    
    # Xóa khoảng trắng thừa và xuống dòng
    code = re.sub(r'\s+', ' ', code)
    code = re.sub(r'\s*([\(\)\{\}\[\]=,;+\-*/%])\s*', r'\1', code)
    
    return code.strip()

def insert_luau_junk_code(code, junk_count=5):
    """Chèn mã rác vào các vị trí ngẫu nhiên trong code Luau"""
    # Tách code thành các câu lệnh
    statements = re.split(r'(;|end|else|elseif|then|do|function)', code)
    
    if len(statements) <= 1:
        return code
    
    junk_statements = generate_luau_junk_statements(junk_count)
    
    # Chèn junk code vào các vị trí ngẫu nhiên
    for junk in junk_statements:
        pos = random.randint(0, len(statements) - 1)
        statements.insert(pos, junk + ';')
    
    return ''.join(statements)

def generate_luau_decryption_code(encrypted_data, keys):
    """Tạo mã giải mã ngắn gọn và hiệu quả cho Luau"""
    # Chuyển dữ liệu đã mã hóa thành chuỗi byte
    byte_array = ','.join(str(b) for b in encrypted_data)
    
    # Tạo mã giải mã tối ưu cho Luau
    decryption_code = []
    
    # Tạo key strings
    key_strings = []
    for i, key in enumerate(keys):
        key_str = '{' + ','.join(str(b) for b in key) + '}'
        key_strings.append(f'k{i}={key_str}')
    
    decryption_code.append(f'local {",".join(key_strings)}')
    
    # Tạo dữ liệu mã hóa
    decryption_code.append(f'local d=string.char(unpack({{{byte_array}}}))')
    
    # Giải mã từng lớp
    for i in range(len(keys)-1, -1, -1):
        key_len = len(keys[i])
        decryption_code.append(f'for i=1,#d do local b=d:byte(i) d=d:sub(1,i-1)..string.char(b~k{i}[(i-1)%{key_len}+1])..d:sub(i+1) end')
    
    decryption_code.append('loadstring(d)()')
    
    return ';'.join(decryption_code)

def obfuscate_luau_advanced(code, junk_amount=5, xor_layers=2):
    """Hàm chính để obfuscate mã Luau - phiên bản tối ưu"""
    try:
        # Bước 1: Đổi tên biến và hàm
        code, mapping = obfuscate_luau_names(code)
        
        # Bước 2: Làm phẳng mã
        code = flatten_luau_code(code)
        
        # Bước 3: Chèn mã rác
        code = insert_luau_junk_code(code, junk_amount)
        
        # Bước 4: Mã hóa nhiều lớp XOR
        encrypted_data, keys = multi_layer_xor(code, xor_layers)
        
        # Bước 5: Tạo mã giải mã và thực thi
        final_code = generate_luau_decryption_code(encrypted_data, keys)
        
        return final_code
    
    except Exception as e:
        raise Exception(f"Lỗi khi obfuscate: {str(e)}")

@app.route('/obfuscate', methods=['POST'])
def obfuscate():
    """Endpoint để obfuscate mã Luau"""
    try:
        # Kiểm tra xem request có phải là JSON không
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
        
        code = data['code']
        junk_amount = data.get('junk_amount', 5)
        xor_layers = data.get('xor_layers', 2)
        
        # Kiểm tra code không rỗng
        if not code.strip():
            return jsonify({'error': 'Code is empty'}), 400
        
        obfuscated_code = obfuscate_luau_advanced(code, junk_amount, xor_layers)
        
        return jsonify({
            'obfuscated_code': obfuscated_code,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/obfuscate_file', methods=['POST'])
def obfuscate_file():
    """Endpoint để obfuscate file Luau"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not (file.filename.endswith('.lua') or file.filename.endswith('.txt') or file.filename.endswith('.luau')):
            return jsonify({'error': 'Invalid file type. Only .lua, .luau, and .txt files are allowed'}), 400
        
        # Đọc và decode file
        code = file.read().decode('utf-8')
        
        # Lấy tham số từ form
        junk_amount = int(request.form.get('junk_amount', 5))
        xor_layers = int(request.form.get('xor_layers', 2))
        
        # Kiểm tra code không rỗng
        if not code.strip():
            return jsonify({'error': 'File is empty'}), 400
        
        obfuscated_code = obfuscate_luau_advanced(code, junk_amount, xor_layers)
        
        # Trả về file đã obfuscate
        output = BytesIO()
        output.write(obfuscated_code.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name='obfuscated_' + file.filename,
            mimetype='text/plain'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint kiểm tra tình trạng server"""
    return jsonify({'status': 'healthy', 'service': 'Luau Obfuscator'})

@app.route('/', methods=['GET'])
def index():
    """Trang chủ"""
    return jsonify({
        'message': 'Luau Obfuscator Server',
        'endpoints': {
            'POST /obfuscate': 'Obfuscate Lua code',
            'POST /obfuscate_file': 'Obfuscate Lua file',
            'GET /health': 'Health check'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
