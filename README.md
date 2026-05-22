# USOS Model Context Protocol (MCP) Server

A standardized Model Context Protocol (MCP) server that bridges the official **USOS API** (Uniwersytecki System Obsługi Studiów) with generative AI clients (such as Claude Code, Claude Desktop, Cursor, and web-based assistants via tunnels). 

This server allows students of Polish universities to query their schedules, track academic grades, monitor ECTS accumulation, search for lecturer contact data, and review study programs through natural language conversations.

---

## 1. Project Overview & Architecture

### The Problem
The USOSweb interface, while functional, presents nested tables, complex directories, and disparate systems for tracking grades, schedules, and program stages. Students frequently navigate multiple sub-menus to compile study progress, locate contact details, or coordinate schedules.

### The Solution: USOS MCP Server
By wrapping the official USOS API in an MCP interface, this server translates complex REST-like endpoints into declarative **Tools**, **Resources**, and **Prompts**. This empowers local LLM agents to act as interactive academic advisors, personal schedulers, and administrative guides.

### Design Principles
*   **Zero Middle-Man Hosting (RODO/GDPR-Shield):** Academic records, grades, and student IDs are highly private data. Because this MCP server runs *locally* on the student's machine, the data flow occurs solely between the university's official API servers and the local client. Your code does not collect or process student data in any external database, radically simplifying RODO compliance.
*   **Multi-Target Architecture:** Rather than hardcoding a single university's system, the server accepts a dynamic base URL and isolated API keys (e.g., University of Warsaw, Jagiellonian University, Warsaw University of Technology).
*   **State Persistence:** OAuth 1.0a access tokens and university profiles are safely persisted in a local configuration file (e.g., `~/.usos-mcp.json`) securely on the student's system.

---

## 2. Comprehensive Use Cases

Below is an expanded suite of 10 primary student-focused use cases spanning grades, timetables, and administration:

### Category A: Core Sessions & Identity
*   **UC-1: OAuth 1.0a Dynamic Handshake (Sign In)**
    *   *System Flow:* Generates a 3-legged or 2-legged request token (`services/oauth/request_token`). It provides a web authorization URL to the student. The student logs in via their central CAS portal, gets a PIN, and pastes it into the chat interface to swap it for a permanent `oauth_token` and `oauth_token_secret`.
*   **UC-2: Student Profile Retrieval**
    *   *System Flow:* Exposes student information such as student ID (index number), faculty membership, email, and current program details.
    *   *Endpoint:* `services/users/user`

### Category B: Time & Timetables
*   **UC-3: Real-time Schedule Assessment**
    *   *System Flow:* Fetches scheduled academic activities (lectures, labs, seminars) for a specified day or week.
    *   *Endpoint:* `services/tt/student` or `services/tt/user`
*   **UC-4: Classgroup Date Resolution**
    *   *System Flow:* Checks exact physical meeting rooms, class types, group numbers, and changes for individual class units.
    *   *Endpoint:* `services/tt/classgroup`
*   **UC-5: Rector/Dean Day Off Calendar Check**
    *   *System Flow:* Cross-checks holidays, rector's hours, or planned exam sessions to clarify schedule changes.
    *   *Endpoint:* `services/calendar/calendar_event`

### Category C: Academic Performance
*   **UC-6: Grade Tracker & GPA Analyst**
    *   *System Flow:* Retrieves grades assigned to specific course editions, exam sessions, or term codes. The LLM can calculate the weighted GPA (using ECTS values as weights) for any semester or overall study program.
    *   *Endpoint:* `services/grades/grade` and `services/grades/course_edition2`
*   **UC-7: Study Programs & Program Stages (ECTS Audit)**
    *   *System Flow:* Fetches the student's active study tracks, milestones, and ECTS requirements. It checks if the student has accumulated enough credits to complete the current program stage.
    *   *Endpoint:* `services/progs/student` and `services/credits/used_sum`
*   **UC-8: Course Cart & Registration Audit**
    *   *System Flow:* Explores courses in the student's registered cart and details about active university registration rounds.
    *   *Endpoint:* `services/registrations/courses_cart`

### Category D: Administration & Infrastructure
*   **UC-9: Lecturer & Staff Directory lookup**
    *   *System Flow:* Searches for staff members, retrieves office rooms, email addresses, and coordinates office hours schedules.
    *   *Endpoint:* `services/users/search` and `services/geo/room`
*   **UC-10: Student Payment and Tuition Tracker**
    *   *System Flow:* Tracks outstanding university balances (e.g., dormitory fees, retake fees, tuition), account numbers, and payment deadlines.
    *   *Endpoint:* `services/payments/payment`

---

## 3. MCP Protocol Mapping (Schema Design)

To implement the use cases above, the server exposes the following MCP schema elements:

### Tools (`tools`)

| Tool Name | Parameters | Purpose / Endpoint mapped |
| :--- | :--- | :--- |
| `get_auth_url` | None | Returns the URL for OAuth 1.0a CAS authentication |
| `authorize_pin` | `pin: string` | Exchanges the verification PIN for an Access Token |
| `get_timetable` | `start_date?: string` (YYYY-MM-DD), `days?: number` | Fetches the student's schedule (`services/tt/user`) |
| `get_grades` | `term_id: string` (e.g., `2025/26Z`) | Retrieves academic grades (`services/grades/course_edition2`) |
| `get_payments` | None | Lists tuition fees, dormitory dues, and deadines (`services/payments/payment`) |
| `search_faculty` | `query: string` | Locates lecturer office rooms, emails, and office hours |

### Resources (`resources`)

*   `usos://student/profile` – Exposes static profile and active study tracks.
*   `usos://student/ects` – Lists current ECTS achievements vs. track requirements.
*   `usos://timetable/today` – A real-time stream containing schedule activities for the current day.

### Prompts (`prompts`)

*   **`study-progress-report`**: Instructs the LLM to access the user's grades and ECTS resources, calculate their Polish academic GPA, identify failed or uncompleted courses, and present a constructive summary.
*   **`plan-my-week`**: Instructs the LLM to cross-reference the user's local timetable and university calendar events to prepare a prioritized list of assignments, class preparations, and commute schedules.

---

## 4. Setup, Deployment & Client Integration

### Prerequisites
1.  **USOS Developer Key:** Log in to your university’s USOSapps developer console (e.g., `https://apps.usos.uw.edu.pl/developers/`) and click "Sign up for an API key" to register your application. Receive your `Consumer Key` and `Consumer Secret`.
2.  **Environment Variables:** Create a `.env` file containing your university's API parameters:
    ```env
    USOS_BASE_URL="https://apps.usos.your-university.edu.pl"
    USOS_CONSUMER_KEY="your_key_here"
    USOS_CONSUMER_SECRET="your_secret_here"
    ```

### Local Client Integrations

#### 1. Claude Code (CLI Agent)
To configure your USOS helper directly inside Claude Code, run:
```bash
claude mcp add usos-assistant --transport stdio --env USOS_BASE_URL="https://apps.usos.edu.pl" -- python /path/to/usos_server.py