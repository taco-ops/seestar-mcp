# Docker Usage Guide

This guide explains how to run the SeestarS50 MCP Server using Docker and Docker Compose.

## � **Docker Workflow**

The project uses Docker Compose as the primary method for containerized deployment.

## 📋 **Current Setup**

### **Docker Compose (Primary Method):**
```bash
SEESTAR_HOST=192.168.1.214 docker-compose up -d    # Build & run
docker-compose logs -f                              # View logs
docker-compose down                                 # Stop
```

### **Manual Docker (Advanced):**
```bash
docker build -t seestar-mcp .                      # Build image
docker run -e SEESTAR_HOST=192.168.1.214 seestar-mcp  # Run container
```

## 🚀 **Recommended Workflows**

### **Development:**
```bash
# Start with live reload for development
SEESTAR_HOST=192.168.1.214 docker-compose up

# Or for background running
SEESTAR_HOST=192.168.1.214 docker-compose up -d
docker-compose logs -f
```

### **Testing:**
```bash
# Test with docker-compose
SEESTAR_HOST=192.168.1.214 docker-compose up --build

# Quick connection test
docker-compose logs seestar-mcp --tail 10
```

### **Production:**
```bash
# Start production deployment
SEESTAR_HOST=your.telescope.ip LOG_LEVEL=INFO docker-compose up -d

# Monitor logs
docker-compose logs -f seestar-mcp

# Update deployment
docker-compose pull && docker-compose up -d
```

## 🛠️ **Docker Compose Benefits**

1. **Simplified Commands**: Single command for build + run
2. **Environment Management**: Easy environment variable handling
3. **Persistence**: Automatic container restart policies
4. **Volume Management**: Consistent log and data mounting
5. **Network Configuration**: Proper host network setup for telescope access

## 🔧 **Advanced Docker Compose Usage**

### **Multiple Environments:**
```bash
# Development with source mounting
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production optimized
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Scaling (Future):**
```bash
# Multiple telescope support
SEESTAR_HOST_1=192.168.1.214 SEESTAR_HOST_2=192.168.1.215 docker-compose up -d
```

## 🧪 **Testing**

### **Container Health Check:**
```bash
# Test with docker-compose
SEESTAR_HOST=192.168.1.214 docker-compose up --build

# Check container logs for health
docker-compose logs seestar-mcp

# Test telescope connection via MCP tools
uv run seestar-mcp --host 192.168.1.214
```

### **Common Issues:**

1. **Network Access**: Ensure telescope IP is reachable
2. **Environment Variables**: Check SEESTAR_HOST is set correctly
3. **Port Conflicts**: MCP server runs on port 4700
4. **Container Resources**: Monitor Docker resource usage
