export type SourceType = 'LIVE' | 'UPLOAD';

export interface Camera {
  id: number;
  name: string;
  source_type: SourceType;
  stream_url: string | null;
  video_file: string | null;
  /** Annotated preview from backend processing (optional). */
  processed_file?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CreateCameraRequest {
  name: string;
  source_type: SourceType;
  stream_url?: string | null;
  video_file?: File | null;
}
