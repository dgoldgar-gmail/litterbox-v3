FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git gcc openssh-client sshpass supervisor \
    && rm -rf /var/lib/apt/lists/*

ENV SCHEDULER_MODE=manager

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app

# 4. Dependency installation (Cached for Multi-Arch efficiency)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY ansible ansible
COPY conf conf
COPY jinja jinja
COPY routes routes
COPY static static
COPY tasks tasks
COPY templates templates
COPY supervisord.conf supervisord.conf

RUN mkdir -p /root/.ssh /app/ansible/queue /app/ansible/results /app/logs && \
    chown -R root:root /app

RUN git config --global user.email "dgoldgar@gmail.com" \
    && git config --global user.name "Dave Goldgar" \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts

EXPOSE 5555

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]