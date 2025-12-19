# Integration Guide - {Project Name}

**For:** End Users  
**Purpose:** Complete setup and configuration guide  
**Last Updated:** {Date}

---

## 🎯 Overview

This guide will help you integrate {Project Name} with Claude Desktop. By the end, you'll be able to {primary use case}.

**Time Required:** 10-15 minutes  
**Difficulty:** Beginner

---

## 📋 Prerequisites

Before you begin, ensure you have:

- [ ] Claude Desktop installed ([Download](https://claude.ai/download))
- [ ] Python 3.10 or higher installed ([Download](https://www.python.org/downloads/))
- [ ] {Additional requirement 1}
- [ ] {Additional requirement 2}
- [ ] {Application/Service} account and API key (if required)

---

## 📦 Installation

### Option 1: MCPB Package (Recommended)

**Easiest method - drag and drop!**

1. **Download the Package**
   - Go to [Releases](https://github.com/your-org/{repo-name}/releases)
   - Download the latest `.mcpb` file

2. **Install to Claude Desktop**
   - Drag the `.mcpb` file onto Claude Desktop
   - Claude will automatically install and configure it

3. **Configure Settings**
   - Claude will prompt for required configuration
   - Enter your API key and other settings

4. **Restart Claude Desktop**
   - Close and reopen Claude Desktop
   - The server will start automatically

---

### Option 2: Install from Source

**For developers or custom setups**

```bash
# 1. Clone the repository
git clone https://github.com/your-org/{repo-name}.git
cd {repo-name}

# 2. Install dependencies (using uv - recommended)
uv sync

# 3. Or install with pip
pip install -e .

# 4. Verify installation
uv run {package-name} --version
```

---

## ⚙️ Configuration

### Claude Desktop Config

**Location:** 
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "{server-name}": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/{repo-name}",
        "run",
        "{package-name}"
      ],
      "env": {
        "API_KEY": "your-api-key-here",
        "TIMEOUT": "30",
        "DEBUG": "false"
      }
    }
  }
}
```

**Important:**
- Replace `/absolute/path/to/{repo-name}` with the actual path
- Replace `your-api-key-here` with your actual API key
- Use forward slashes (`/`) even on Windows for the directory path

---

### Environment Variables

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `API_KEY` | ✅ Yes | - | API key for {service} | `sk-abc123...` |
| `TIMEOUT` | ⬜ No | `30` | Request timeout (seconds) | `60` |
| `DEBUG` | ⬜ No | `false` | Enable debug logging | `true` |
| {CUSTOM_VAR} | ⬜ No | {default} | {Description} | {example} |

**How to Get an API Key:**

1. Go to {service website}
2. Sign up or log in
3. Navigate to API settings
4. Generate a new API key
5. Copy and paste into configuration

---

## ✅ Verification

### Step 1: Restart Claude Desktop

Close Claude Desktop completely and reopen it.

### Step 2: Check Connection

Ask Claude:
```
"What {server-name} tools are available?"
```

**Expected Response:**
Claude should list the available tools, such as:
- `{tool1}` - {Description}
- `{tool2}` - {Description}
- `{tool3}` - {Description}

### Step 3: Test Basic Operation

Try a simple operation:
```
"{Example query that uses your tool}"
```

**Expected Response:**
{Description of what should happen}

---

## 🎯 First Steps

### Basic Usage Examples

#### Example 1: {Use Case 1}

**Ask Claude:**
```
"{Example query 1}"
```

**What Happens:**
- {Step 1}
- {Step 2}
- {Step 3}

**Result:**
{Description of result}

---

#### Example 2: {Use Case 2}

**Ask Claude:**
```
"{Example query 2}"
```

**What Happens:**
- {Step 1}
- {Step 2}
- {Step 3}

**Result:**
{Description of result}

---

#### Example 3: {Use Case 3}

**Ask Claude:**
```
"{Example query 3}"
```

**What Happens:**
- {Step 1}
- {Step 2}
- {Step 3}

**Result:**
{Description of result}

---

## 🔧 Common Use Cases

### Use Case: {Common Task 1}

**Scenario:** {Description}

**Steps:**
1. Ask Claude: `"{query}"`
2. Claude will {action}
3. Review the results
4. {Follow-up action if needed}

**Tips:**
- {Tip 1}
- {Tip 2}

---

### Use Case: {Common Task 2}

**Scenario:** {Description}

**Steps:**
1. {Step 1}
2. {Step 2}
3. {Step 3}

**Tips:**
- {Tip 1}
- {Tip 2}

---

## 🎨 Advanced Configuration

### Custom Timeouts

For operations that take longer:

```json
{
  "env": {
    "API_KEY": "your-key",
    "TIMEOUT": "120"
  }
}
```

### Debug Mode

To troubleshoot issues:

```json
{
  "env": {
    "API_KEY": "your-key",
    "DEBUG": "true"
  }
}
```

**View Logs:**
- Windows: `%LOCALAPPDATA%\Claude\logs\`
- macOS: `~/Library/Logs/Claude/`
- Linux: `~/.local/share/Claude/logs/`

### Multiple Instances

To use multiple configurations:

```json
{
  "mcpServers": {
    "{server-name}-production": {
      "command": "uv",
      "args": ["--directory", "/path/to/{repo-name}", "run", "{package-name}"],
      "env": {"API_KEY": "prod-key"}
    },
    "{server-name}-staging": {
      "command": "uv",
      "args": ["--directory", "/path/to/{repo-name}", "run", "{package-name}"],
      "env": {"API_KEY": "staging-key"}
    }
  }
}
```

---

## 🔒 Security Best Practices

### API Key Management

- ✅ **DO:** Store API keys in environment variables
- ✅ **DO:** Use different keys for development/production
- ✅ **DO:** Rotate keys regularly
- ❌ **DON'T:** Commit API keys to version control
- ❌ **DON'T:** Share keys in screenshots or logs

### Permissions

- Review what data the server can access
- Use minimal required permissions
- Regularly audit access logs

---

## 🐛 Troubleshooting

### Issue: "Server not found" or "Connection failed"

**Symptoms:**
- Claude can't find the server
- No tools are available

**Solutions:**
1. Check the config file path is correct
2. Verify the `command` path is absolute
3. Restart Claude Desktop
4. Check logs for errors

**Verify Command:**
```bash
# Test the command manually
uv --directory /path/to/{repo-name} run {package-name} --version
```

---

### Issue: "Authentication failed" or "API key invalid"

**Symptoms:**
- Tools are available but return auth errors
- "Invalid API key" messages

**Solutions:**
1. Verify API key is correct
2. Check API key hasn't expired
3. Ensure no extra spaces in key
4. Generate a new API key

---

### Issue: "Timeout" errors

**Symptoms:**
- Operations take too long
- Timeout errors

**Solutions:**
1. Increase timeout in configuration:
   ```json
   {"env": {"TIMEOUT": "120"}}
   ```
2. Check internet connection
3. Verify external service is responding

---

### Issue: Server starts but tools don't work

**Symptoms:**
- Tools are listed but fail when used
- Error messages when calling tools

**Solutions:**
1. Enable debug mode
2. Check logs for specific errors
3. Verify all prerequisites are installed
4. Test external services manually

---

## 📚 Next Steps

### Learn More

- [Architecture Documentation](architecture.md) - Understand how it works
- [Tool Reference](tools-reference.md) - Complete API documentation
- [Examples](examples/) - More usage examples
- [Troubleshooting](troubleshooting.md) - Detailed troubleshooting guide

### Get Help

- **Issues:** [GitHub Issues](https://github.com/your-org/{repo-name}/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/{repo-name}/discussions)
- **Email:** support@example.com

---

## 🎉 Success!

You're now ready to use {Project Name} with Claude Desktop!

**Try asking Claude:**
- `"{Suggested query 1}"`
- `"{Suggested query 2}"`
- `"{Suggested query 3}"`

---

**Guide Version:** 1.0  
**Last Updated:** {Date}  
**Feedback:** [Report issues or suggestions](https://github.com/your-org/{repo-name}/issues)

