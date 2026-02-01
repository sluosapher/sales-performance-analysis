## Sales Performance Analysis

This tool now provides a combined web interface and an MCP server to read raw sales data from Excel workbooks and generate geo-based “Top 10” summary reports. It features user authentication with roles, per-user access tokens for AI agents, and a dedicated admin interface for user management.

### Requirements
- Python 3.12 or later
- All dependencies listed in `pyproject.toml` installed (managed with `uv sync`)

### Setup and Initialization
To get the application ready for use, follow these steps:

1.  **Install Dependencies:**
    Ensure all project dependencies are installed using `uv`:
    ```bash
    uv sync
    ```

2.  **Initialize Database and Create Test Users:**
    This step creates the SQLite database (`data/users.db`) and populates it with default admin and test user accounts. The system will print their usernames, passwords, and MCP tokens to the console.
    ```bash
    uv run python init_db.py
    ```
    *Default Test Users (change passwords on first login for security):*
    *   `admin` / `admin123` (Admin role, full access)
    *   `uploader` / `upload123` (Regular user, can upload files and list/view/download results)
    *   `user` / `user123` (Regular user, can only list/view/download results)

### Running the Application (Web UI & MCP Server)
To start both the Flask web interface and the MCP server:
```bash
uv run python app.py
```
The **Web Interface** will be available at `http://localhost:8004` and the **MCP Server** at `http://localhost:8003`.

### Web Interface Usage (Browser)

Open your web browser and navigate to `http://localhost:8004`.

1.  **Login:** You will be prompted to log in. Use one of the test user credentials created during database initialization.
2.  **Permissions:**
    *   **Admin Users:** Have access to all features including file upload, viewing results, and the **User Management** panel under `/admin/users` to add/edit/delete users and regenerate their tokens.
    *   **Uploader Users:** Can upload new data files via `/upload` and access the reports under `/list-results`.
    *   **Regular Users:** Can only view and download existing reports under `/list-results`.
3.  **Profile Page (`/profile`):** All authenticated users can access their profile to view their unique **MCP Access Token** and change their password.

### AI Agent (MCP) Usage

AI agents (such as Claude Code) can interact with the MCP server to programmatically upload sales data or retrieve reports. Authentication is performed using a per-user secret token.

1.  **Obtain Your Token:** Log into the web interface with your user credentials, go to your `/profile` page, and copy your unique **MCP Access Token**.
2.  **Authenticate MCP Requests:** Include your token in the `Authorization` header of your HTTP requests as a Bearer token.

    *Example using `curl` to list results:*
    ```bash
    curl -H "Authorization: Bearer YOUR_SECRET_TOKEN_HERE" http://localhost:8003/list-results
    ```
    Replace `YOUR_SECRET_TOKEN_HERE` with the actual token from your profile page.

### Original CLI Usage (main.py)

For command-line only batch processing (without the web interface or MCP server, using a local raw data file) you can still use `main.py`:

```bash
uv run python main.py --output <output.xlsx> [--input <input.xlsx>]
```

Examples:
- `uv run python main.py --input raw_data_1103.xlsx --output report.xlsx`
- `uv run python main.py --output output\report.xlsx` (auto-selects latest `raw_data_YYMMDD.xlsx` from the `input` folder)

### Prepare Input Data
- Place your raw Excel workbooks in the `input` folder at the project root (created automatically).
- Name input files using the pattern `raw_data_YYMMDD.xlsx` (for example, `raw_data_251103.xlsx` for 2025‑11‑03); this timestamp is used to pick the latest file and to name history reports.
- When you omit `--input`, the tool automatically selects the latest `raw_data_YYMMDD.xlsx` from the `input` folder.

### Expected Output
The program writes several worksheets to the output workbook, whether generated via the web UI, MCP, or CLI:
- `Top 10 Sales by Geo` (default): Top 10 salespeople per Geo (AP, BRAZIL, EMEA, LAS, MX, NA) with per-quarter revenue and totals.
- `Top 10 ThinkShield by Geo` (default): Same structure, filtered to the `ThinkShield Security` offering.
- `Top 10% All` (default): Per-geo tables showing total revenue, top 10 revenue, and the percentage represented by the top 10.
- `Top 10% Security` (default): The same percentage tables, restricted to ThinkShield revenue.

Sheet names can be customized with optional flags (for `main.py` CLI only, see `uv run python main.py --help`).
