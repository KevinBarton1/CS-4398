import { useCallback, useEffect, useRef } from "react";

export interface ToastMessage {
  detail: string;
  guidance?: string;
  variant: "info" | "error";
  onRetry?: () => void;
}

interface ToastProps {
  message: ToastMessage | null;
  onDismiss: () => void;
}

const AUTO_DISMISS_MS = 6000;

export function Toast({ message, onDismiss }: ToastProps) {
  const timerRef = useRef<number | undefined>(undefined);
  const pausedRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== undefined) {
      window.clearTimeout(timerRef.current);
      timerRef.current = undefined;
    }
  }, []);

  const startTimer = useCallback(() => {
    clearTimer();
    if (!message || pausedRef.current) {
      return;
    }
    timerRef.current = window.setTimeout(() => {
      onDismiss();
    }, AUTO_DISMISS_MS);
  }, [clearTimer, message, onDismiss]);

  useEffect(() => {
    pausedRef.current = false;
    startTimer();
    return clearTimer;
  }, [message, startTimer, clearTimer]);

  const handlePause = () => {
    pausedRef.current = true;
    clearTimer();
  };

  const handleResume = () => {
    pausedRef.current = false;
    startTimer();
  };

  const role = message?.variant === "error" ? "alert" : "status";

  return (
    <div className="toast-layer" aria-label="Notifications" aria-live="polite">
      <div
        className={`toast${message ? " toast--visible" : ""}`}
        role={message ? role : undefined}
        aria-atomic="true"
        onMouseEnter={handlePause}
        onMouseLeave={handleResume}
        onFocus={handlePause}
        onBlur={handleResume}
      >
        {message ? (
          <>
            <p className="toast__detail">{message.detail}</p>
            {message.guidance ? <p className="toast__guidance">{message.guidance}</p> : null}
            {message.onRetry ? (
              <button type="button" className="link-button toast__retry" onClick={message.onRetry}>
                Retry
              </button>
            ) : null}
            <button type="button" className="toast__dismiss" onClick={onDismiss} aria-label="Dismiss notification">
              ×
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}
