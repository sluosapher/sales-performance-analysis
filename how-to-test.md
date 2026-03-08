 1. Initialize the Database: Run python init_db.py from your terminal.
  2. Start the Flask Application: Run python app.py. This will start both the Flask web server (port 8004) and the MCP server (port
  8003).
  3. Test Web Login and Permissions: Use your browser to interact with the web interface at http://localhost:8004/.
    - Test logging in with admin/admin123, user/user123, and uploader/upload123 to verify navigation, permissions, and admin
  functionalities.
    - Change passwords and regenerate tokens via the profile page and admin interface.
  4. Test MCP Server Token Verification: Obtain a user's secret token from the web interface's /profile page (or admin page) and test
  the MCP endpoints using curl as described in the detailed plan.
