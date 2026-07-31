interface StatusBannerProps {
  detail: string;
  onRetry?: () => void;
  region?: string;
}

export function StatusBanner({ detail, onRetry, region = "map" }: StatusBannerProps) {
  return (
    <div className="status-banner" role="alert" aria-label={`${region} status`}>
      <p>{detail}</p>
      {onRetry ? (
        <button type="button" className="link-button" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
