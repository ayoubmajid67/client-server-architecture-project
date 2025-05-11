import uuid
from datetime import datetime

def generate_task_id():
    return str(uuid.uuid4())

def current_time():
    return datetime.utcnow().isoformat()

def validate_expression(expr):
    allowed = "0123456789+-*/(). "
    return all(c in allowed for c in expr)

def evaluate_expression(expr):
    try:
        return str(eval(expr, {"__builtins__": None}, {}))
    except:
        return "Error"

def get_request_server_port(request):
    server_ip = request.host.split(':')[0]
    server_port = request.host.split(':')[1] if ':' in request.host else '80'
    return server_ip, server_port