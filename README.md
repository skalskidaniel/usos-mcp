# USOS Model Context Protocol (MCP) Server

A standardized Model Context Protocol (MCP) server that bridges the official **USOS API** (Uniwersytecki System Obsługi Studiów) with generative AI clients (such as Claude Code, Claude Desktop, Cursor, and web-based assistants via tunnels). 

This server allows students of Polish universities to query their schedules, track academic grades, monitor ECTS accumulation, search for lecturer contact data, and review study programs through natural language conversations.

---

## Project Overview & Architecture

### The Problem
The USOSweb interface, while functional, presents nested tables, complex directories, and disparate systems for tracking grades, schedules, and program stages. Students frequently navigate multiple sub-menus to compile study progress, locate contact details, or coordinate schedules.

### The Solution: USOS MCP Server
By wrapping the official USOS API in an MCP interface, this server translates complex REST-like endpoints into declarative **Tools**, **Resources**, and **Prompts**. This empowers local LLM agents to act as interactive academic advisors, personal schedulers, and administrative guides.

### Design Principles
*   **Zero Middle-Man Hosting (RODO/GDPR-Shield):** Academic records, grades, and student IDs are highly private data. Because this MCP server runs *locally* on the student's machine, the data flow occurs solely between the university's official API servers and the local client. Your code does not collect or process student data in any external database, radically simplifying RODO compliance.
*   **Multi-Target Architecture:** Rather than hardcoding a single university's system, the server accepts a dynamic base URL and isolated API keys (e.g., University of Warsaw, Jagiellonian University, Warsaw University of Technology).
*   **State Persistence:** OAuth 1.0a access tokens and university profiles are safely persisted in a local configuration file (e.g., `~/.usos-mcp.json`) securely on the student's system.