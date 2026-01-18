# Use a slim python base
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    gcc \
    openssh-client \
    sshpass \
    supervisor \
    && rm -rf /var/lib/apt/lists/*



WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -s /bin/bash dgoldgar

RUN mkdir -p /home/dgoldgar/.ssh \
 && chown -R dgoldgar:dgoldgar /home/dgoldgar \
 && chown -R dgoldgar:dgoldgar /app

USER dgoldgar

RUN git config --global user.email "dgoldgar@gmail.com" \
  && git config --global user.name "Dave Goldgar" \
  && ssh-keyscan github.com >> /home/dgoldgar/.ssh/known_hosts


RUN mkdir -p ansible/queue ansible/results logs

RUN chmod +x ansible_worker.py

EXPOSE 5555

CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]
