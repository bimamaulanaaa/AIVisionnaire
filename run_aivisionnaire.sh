#!/bin/bash

# Set variables
APP_DIR=$(pwd)
LOG_FILE="$APP_DIR/app.log"
VENV_DIR="$APP_DIR/venv"
PID_FILE="$APP_DIR/.app_pid"

# Function to display help
show_help() {
    echo "AI Visionnaire Management Script"
    echo "--------------------------------"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the application"
    echo "  stop        - Stop the application"
    echo "  restart     - Restart the application"
    echo "  status      - Check if the application is running"
    echo "  logs        - Show the application logs"
    echo "  test        - Run the Pinecone test script"
    echo "  help        - Show this help message"
    echo ""
}

# Function to start the application
start_app() {
    echo "Starting AI Visionnaire..."
    
    # Check if app is already running
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
        echo "Application is already running with PID $(cat "$PID_FILE")"
        return 0
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || {
        echo "Failed to activate virtual environment"
        return 1
    }
    
    # Start the application
    nohup python gradio-frontend.py > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # Save PID to file
    echo $PID > "$PID_FILE"
    
    echo "Application started with PID $PID"
    echo "Logs available at $LOG_FILE"
    
    # Deactivate virtual environment
    deactivate
}

# Function to stop the application
stop_app() {
    echo "Stopping AI Visionnaire..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        
        if ps -p $PID > /dev/null; then
            echo "Killing process $PID..."
            kill $PID
            sleep 2
            
            # Force kill if still running
            if ps -p $PID > /dev/null; then
                echo "Process still running, force killing..."
                kill -9 $PID
            fi
            
            echo "Application stopped"
        else
            echo "No running process found with PID $PID"
        fi
        
        rm "$PID_FILE"
    else
        echo "No PID file found, trying to find and kill the process..."
        pkill -f "python gradio-frontend.py"
        echo "Any running instances should be stopped now"
    fi
}

# Function to restart the application
restart_app() {
    echo "Restarting AI Visionnaire..."
    stop_app
    sleep 2
    start_app
}

# Function to check application status
check_status() {
    if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null; then
        echo "Application is running with PID $(cat "$PID_FILE")"
        echo "You can access it at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):7861"
    else
        echo "Application is not running"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "Showing last 50 lines of logs (Press Ctrl+C to exit):"
        tail -n 50 -f "$LOG_FILE"
    else
        echo "Log file not found"
    fi
}

# Function to run Pinecone test
run_test() {
    echo "Running Pinecone test..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate" || {
        echo "Failed to activate virtual environment"
        return 1
    }
    
    # Run the test with provided arguments
    python test_pinecone.py "$@"
    
    # Deactivate virtual environment
    deactivate
}

# Main logic
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    test)
        shift  # Remove the "test" argument
        run_test "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

exit 0 