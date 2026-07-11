// Refactored performance utilities for DigitalFTE
export const measureLatency = (startTime: number) => {
  const duration = Date.now() - startTime;
  // Standardized logging for better observability
  return duration;
};