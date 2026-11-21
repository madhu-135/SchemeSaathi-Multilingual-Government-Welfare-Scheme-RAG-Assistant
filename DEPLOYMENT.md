# SchemeSaathi Deployment Guide 🚀

This guide provides step-by-step instructions to deploy SchemeSaathi to:
1. **Render (PaaS - Cloud Hosted)**
2. **Free-Tier VPS (Oracle Cloud Always Free / AWS EC2 Free Tier / Hetzner)**

---

## 📋 Required Environment Variables

Before deploying, ensure you have the following secrets and parameters:

| Variable | Description | Example / Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key (*Required*) | `sk-ant-api03-...` |
| `ANTHROPIC_MODEL` | Claude model version | `claude-3-5-sonnet-20241022` |
| `MONGO_URI` | MongoDB connection URI | `mongodb://mongo:27017` (Docker) or `mongodb+srv://...` (Cloud) |
| `MONGO_DB_NAME` | Database name | `schemesaathi` |
| `EMBED_MODEL` | Embedding model | `intfloat/multilingual-e5-small` |
| `TOP_K` | Top chunks to retrieve | `4` |
| `SIMILARITY_THRESHOLD` | Cosine similarity cutoff | `0.80` |
| `PORT` | Web server port | `8000` (Backend default) / `10000` (Render) |

---

## 🌐 Option 1: Deploy to Render

Render offers free web service tiers and static site hosting.

### Step 1: Prepare MongoDB Atlas (Free M0 Sandbox)
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and create a free account.
2. Create a free **M0 Sandbox** cluster (choose AWS or Google Cloud, region closest to your users, e.g. Mumbai / Singapore / Frankfurt).
3. Under **Database Access**, create a user (e.g. `schemesaathi_user`) with a strong password.
4. Under **Network Access**, add IP `0.0.0.0/0` (allow access from anywhere) so Render instances can connect.
5. Click **Connect** $\rightarrow$ **Drivers** $\rightarrow$ Copy the connection string:
   ```text
   mongodb+srv://schemesaathi_user:<password>@cluster0.abcde.mongodb.net/schemesaathi?retryWrites=true&w=majority
   ```

### Step 2: Deploy Backend as a Render Web Service
1. Push your repository to GitHub.
2. Sign in to [Render Dashboard](https://dashboard.render.com/) and click **New +** $\rightarrow$ **Web Service**.
3. Connect your GitHub repository.
4. Fill in the service configuration:
   - **Name**: `schemesaathi-backend`
   - **Language**: `Docker`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Docker Context**: `.` (root of repo)
   - **Instance Type**: `Free` (or Starter for persistent RAM)
5. Under **Health Check Path**:
   - Set to: `/health`
6. Under **Environment Variables**, add:
   - `ANTHROPIC_API_KEY`: `your_actual_anthropic_api_key`
   - `MONGO_URI`: `mongodb+srv://...` (from Step 1)
   - `MONGO_DB_NAME`: `schemesaathi`
   - `EMBED_MODEL`: `intfloat/multilingual-e5-small`
   - `TOP_K`: `4`
   - `SIMILARITY_THRESHOLD`: `0.80`
7. Click **Create Web Service**.
8. Render will build the Docker container (pre-downloading the E5 model) and start Uvicorn. Once active, note your backend URL:
   `https://schemesaathi-backend.onrender.com`

Verify backend health:
```bash
curl https://schemesaathi-backend.onrender.com/health
```

### Step 3: Deploy Frontend as a Render Static Site
1. On Render Dashboard, click **New +** $\rightarrow$ **Static Site**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `schemesaathi-ui`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. Under **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://schemesaathi-backend.onrender.com` (your backend URL from Step 2)
5. Click **Create Static Site**.
6. Render will build the Vite React application and publish it with global CDN and SSL.

---

## 🖥️ Option 2: Deploy to a Free-Tier VPS

Ideal for **Oracle Cloud Always Free** (4 OCPU ARM Ampere + 24GB RAM, or AMD micro), **AWS EC2 Free Tier** (t2/t3.micro), or a low-cost VPS ($3–$5/mo on Hetzner).

### Step 1: Launch & Connect to VPS
Launch an **Ubuntu 22.04 LTS** or **Ubuntu 24.04 LTS** instance. Connect via SSH:
```bash
ssh -i ~/.ssh/id_rsa ubuntu@<YOUR_VPS_PUBLIC_IP>
```

### Step 2: Install Docker & Docker Compose
```bash
# Update package repositories
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker and Docker Compose plugin
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable and start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add ubuntu user to docker group (optional, avoids typing sudo)
sudo usermod -aG docker $USER
```

### Step 3: Clone Repository & Configure `.env`
```bash
# Clone repository
git clone https://github.com/your-username/schemesaathi.git /opt/schemesaathi
cd /opt/schemesaathi

# Create production .env file
cp .env.example .env
nano .env
```
Fill in your secrets:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=schemesaathi
EMBED_MODEL=intfloat/multilingual-e5-small
TOP_K=4
SIMILARITY_THRESHOLD=0.80
```

### Step 4: Verify Pre-Indexed Data
Ensure your vector index files exist in `/opt/schemesaathi/data/index/`:
- `chunks.jsonl`
- `faiss_index.bin`
- `chunks_metadata.json`

*(If starting fresh, run `python -m app.ingest` and `python -m app.vectorstore --build`)*

### Step 5: Launch Services via Docker Compose
```bash
# Build and start all 3 containers in detached mode
sudo docker compose up -d --build
```

Check running container status:
```bash
sudo docker compose ps
```
Expected output:
```text
NAME                   IMAGE                  COMMAND                  SERVICE    STATUS
schemesaathi-mongo     mongo:7.0              "docker-entrypoint.s…"   mongo      running (healthy)
schemesaathi-backend   schemesaathi-backend   "/bin/sh -c 'uvicorn…"   backend    running (healthy)
schemesaathi-frontend  schemesaathi-frontend  "/docker-entrypoint.…"   frontend   running (healthy)
```

### Step 6: Test Health Check & Endpoints
```bash
# Internal health check
curl http://localhost:8000/health

# Frontend proxy check
curl -I http://localhost:3000/
```

### Step 7: Configure Firewall & Security
If running on Ubuntu with `ufw`:
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Frontend (optional if using host Nginx)
sudo ufw enable
```
*(On Oracle Cloud / AWS, also ensure Ports 80, 443, and 3000 are open in the Cloud Ingress Security Rules).*

### Step 8: Setup Domain & Free SSL (Let's Encrypt / Certbot)
To serve SchemeSaathi over standard HTTPS (`https://yourdomain.com`):

Install host Nginx and Certbot:
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/schemesaathi`:
```nginx
server {
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and obtain SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/schemesaathi /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically configure HTTPS redirect and set up auto-renewal cron jobs.

---

## 🩺 Health Check & Monitoring Commands

### Real-Time Logs:
```bash
# Stream backend logs
docker compose logs -f backend

# Stream frontend reverse proxy logs
docker compose logs -f frontend

# Stream mongo logs
docker compose logs -f mongo
```

### Container Health Status:
```bash
docker inspect --format='{{json .State.Health.Status}}' schemesaathi-backend
# Output: "healthy"
```

### Restart / Update Containers:
```bash
# Graceful restart
docker compose restart

# Pull code updates and rebuild
git pull origin main
docker compose up -d --build
```

