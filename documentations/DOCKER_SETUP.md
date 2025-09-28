# Docker Setup with PostgreSQL

This document explains how to run the ChatGPT-like application using Docker with PostgreSQL database.

## 🐳 Docker Services

The `docker-compose.yml` includes:

- **PostgreSQL Database**: Persistent data storage
- **Chatbot Application**: FastAPI application with DDD/Hexagonal Architecture

## 🚀 Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 2. Access the Application

- **Frontend**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

### 3. Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (⚠️ This will delete all data!)
docker-compose down -v
```

## 🔧 Configuration

### Environment Variables

The application automatically detects the database type:

- **PostgreSQL**: Uses `DATABASE_URL` environment variable
- **SQLite**: Falls back to SQLite if no PostgreSQL URL is provided

### Database Configuration

PostgreSQL is configured with:
- **Database**: `chatgpt_db`
- **User**: `chatgpt_user`
- **Password**: `chatgpt_password`
- **Port**: `5432`

### Custom Database URL

To use a different PostgreSQL instance:

```bash
export DATABASE_URL="postgresql+asyncpg://your_user:your_password@your_host:5432/your_database"
docker-compose up --build
```

## 📊 Database Schema

The application automatically creates these tables:

- **users**: User information
- **conversations**: Conversation metadata
- **messages**: Individual messages

## 🔍 Monitoring

### Health Checks

Both services include health checks:

- **PostgreSQL**: `pg_isready` command
- **Application**: HTTP health endpoint

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs chatbot
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f chatbot
```

## 🛠️ Development

### Rebuild After Changes

```bash
# Rebuild and restart
docker-compose up --build --force-recreate

# Rebuild specific service
docker-compose build chatbot
docker-compose up chatbot
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U chatgpt_user -d chatgpt_db

# Run database initialization manually
docker-compose exec chatbot python init_db.py
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check if PostgreSQL is running: `docker-compose ps`
   - Verify database URL in environment variables

2. **Application Won't Start**
   - Check logs: `docker-compose logs chatbot`
   - Ensure PostgreSQL is healthy before starting app

3. **Port Conflicts**
   - Change ports in `docker-compose.yml` if 8000 or 5432 are in use

### Reset Everything

```bash
# Stop, remove containers, networks, and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up --build
```

## 📈 Production Considerations

For production deployment:

1. **Change default passwords**
2. **Use environment files** (`.env`)
3. **Configure proper networking**
4. **Set up monitoring and logging**
5. **Use Docker secrets** for sensitive data
6. **Configure backup strategies**

## 🔗 Related Files

- `docker-compose.yml`: Service definitions
- `Dockerfile`: Application container
- `init_db.py`: Database initialization
- `chat_app/infrastructure/postgresql_repositories.py`: PostgreSQL implementation
