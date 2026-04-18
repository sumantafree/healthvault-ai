# HealthVault AI — Gunicorn Configuration
# Used by systemd service to run FastAPI in production

import multiprocessing

# Server socket
bind        = "127.0.0.1:8000"
backlog     = 2048

# Workers — formula: (2 × CPU cores) + 1
workers     = multiprocessing.cpu_count() * 2 + 1
worker_class= "uvicorn.workers.UvicornWorker"
threads     = 2
timeout     = 300       # 5 min — allows long AI processing
keepalive   = 5

# Logging
loglevel    = "info"
accesslog   = "/var/log/healthvault/access.log"
errorlog    = "/var/log/healthvault/error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name   = "healthvault-api"

# Graceful restart
graceful_timeout = 30
max_requests      = 1000
max_requests_jitter = 50

# Security
limit_request_line   = 4094
limit_request_fields = 100
