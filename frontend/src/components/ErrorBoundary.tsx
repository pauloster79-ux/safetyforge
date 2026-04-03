import { Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex min-h-screen items-center justify-center"
          style={{ backgroundColor: 'var(--concrete-50)', fontFamily: "'IBM Plex Sans', sans-serif" }}
        >
          <div
            className="w-full max-w-md p-7"
            style={{
              backgroundColor: 'var(--white, #ffffff)',
              border: '1px solid var(--concrete-100, #e6e8e3)',
              borderRadius: '0px',
            }}
          >
            <h1
              className="mb-3"
              style={{
                fontSize: '20px',
                fontWeight: 700,
                color: 'var(--black, #0d0e0c)',
              }}
            >
              Something went wrong
            </h1>
            <p
              className="mb-6"
              style={{
                fontSize: '13px',
                fontWeight: 400,
                color: 'var(--concrete-500, #545951)',
                lineHeight: '1.5',
              }}
            >
              An unexpected error occurred. Please try reloading the page. If the
              problem persists, contact support.
            </p>
            {this.state.error && (
              <pre
                className="mb-6 overflow-auto p-3"
                style={{
                  fontSize: '11px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  color: 'var(--concrete-400, #71766b)',
                  backgroundColor: 'var(--concrete-50, #f4f5f3)',
                  border: '1px solid var(--concrete-100, #e6e8e3)',
                  borderRadius: '0px',
                  maxHeight: '120px',
                }}
              >
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReload}
              className="w-full cursor-pointer"
              style={{
                backgroundColor: 'var(--machine, #F5B800)',
                color: 'var(--black, #0d0e0c)',
                border: '1px solid var(--machine-dark, #D9A200)',
                borderRadius: '3px',
                padding: '12px 16px',
                fontSize: '13px',
                fontWeight: 600,
                fontFamily: "'IBM Plex Sans', sans-serif",
              }}
              onMouseOver={(e) => {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor =
                  'var(--machine-bright, #FFCA18)';
              }}
              onMouseOut={(e) => {
                (e.currentTarget as HTMLButtonElement).style.backgroundColor =
                  'var(--machine, #F5B800)';
              }}
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
