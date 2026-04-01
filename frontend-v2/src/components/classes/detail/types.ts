export interface SessionActionPermissions {
  can_start_checkin: boolean
  can_end_checkin: boolean
  can_start_checkout: boolean
  can_end_checkout: boolean
  can_skip: boolean
}

export interface CurrentSession {
  course_id: number
  course_name: string
  session_id: string
  session_label: string
  date: string
  time_range: string
  status: string
  location?: string
  primary_instructor_id?: number
  primary_instructor_name?: string
  action_permissions?: SessionActionPermissions
  checkin_mode?: 'direct' | 'qr' | null
  checkin_duration_minutes?: number | null
  checkin_deadline?: string | null
  checkout_mode?: 'direct' | 'qr' | null
  checkout_duration_minutes?: number | null
  checkout_deadline?: string | null
}

export interface ScheduleItem {
  date: string
  time_range: string
  location?: string
  status?: string
  session_id?: string
  hours?: number
}

export interface CourseItem {
  course_key?: string
  name: string
  type?: string
  instructor?: string
  hours?: number
  schedules?: ScheduleItem[]
}

export interface StudentItem {
  user_id: number
  user_name?: string
  user_nickname?: string
  departments?: string[]
  status?: string
  checkin_rate?: number | null
}

export interface CheckinRecord {
  user_id: number
  user_name?: string
  user_nickname?: string
  status: string
  time?: string
  date?: string
  session_key?: string
  checkout_time?: string
  checkout_status?: string
}

export interface NoticeItem {
  id: number
  title: string
  content?: string
  author_name?: string
  created_at?: string
}

export interface ActivityItem {
  id: number
  training_id: number
  user_id: number | null
  user_name: string | null
  action_type: string
  content: string
  extra_json: Record<string, unknown> | null
  created_at: string | null
}
