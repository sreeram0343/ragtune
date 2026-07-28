"""
RAGTUNE - Main Application Entry Point
Launches Enterprise Web Server or runs CLI Intelligence queries.
"""

import sys
import argparse
import uvicorn
from config.settings import settings
from demo_data.seed_data import seed_enterprise_db, seed_sample_documents


def main():
    parser = argparse.ArgumentParser(description="RAGTUNE Enterprise Knowledge Intelligence Platform")
    parser.add_argument("--server", action="store_true", default=True, help="Launch FastAPI Web Gateway Server")
    parser.add_argument("--host", type=str, default=settings.HOST, help="Server host IP")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Server port number")
    parser.add_argument("--seed", action="store_true", help="Seed enterprise database and sample documents")
    parser.add_argument("--query", type=str, help="Execute a single CLI query through RAGTUNE engine")

    args = parser.parse_args()

    if args.seed:
        print("Seeding enterprise database and documents...")
        seed_enterprise_db()
        seed_sample_documents()
        print("Seed completed successfully.")
        return

    if args.query:
        from api.main import orchestrator, get_default_user_context, AgentState
        user_ctx = get_default_user_context()
        state = AgentState(user_query=args.query, user_context=user_ctx)
        final_state = orchestrator.execute_workflow(state)

        print("\n" + "=" * 60)
        print(f"QUERY: {args.query}")
        print(f"INTENT ROUTE: {final_state.intent_route}")
        print(f"CONFIDENCE: {final_state.overall_confidence * 100:.1f}%")
        print(f"EXECUTION LATENCY: {final_state.execution_time_ms} ms")
        if final_state.sanitized_sql:
            print(f"GENERATED SQL: {final_state.sanitized_sql}")
        print("=" * 60)
        print("SYNTHESIZED NARRATIVE OUTPUT:")
        print(final_state.final_response)
        print("=" * 60 + "\n")
        return

    # Default action: launch server
    print(f"Starting {settings.APP_NAME} v{settings.VERSION} on http://{args.host}:{args.port}")
    uvicorn.run("api.main:app", host=args.host, port=args.port, reload=settings.DEBUG)


if __name__ == "__main__":
    main()
