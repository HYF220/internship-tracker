/**
 * API 工具模块
 *
 * 负责：
 * 1. 管理 JWT token（保存、读取、自动附带）
 * 2. 封装所有后端 API 调用
 */

// ==================== Token 管理 ====================

const TOKEN_KEY = "auth_token";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn(): boolean {
  return getToken() !== null;
}

// ==================== 通用请求函数 ====================

async function request(method: string, path: string, body?: object): Promise<Response> {
  const headers: Record<string, string> = {};

  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options: RequestInit = {
    method,
    headers,
  };

  if (body) {
    options.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  const response = await fetch(path, options);

  // 如果 token 过期，清除并跳转登录页
  if (response.status === 401) {
    clearToken();
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }

  return response;
}

async function apiGet(path: string) {
  const res = await request("GET", path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiPost(path: string, body?: object | FormData) {
  const res = await request("POST", path, body);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

async function apiPut(path: string, body?: object) {
  const res = await request("PUT", path, body);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function apiDelete(path: string) {
  const res = await request("DELETE", path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return null;
}

// ==================== 类型定义 ====================

export interface Job {
  id: number;
  user_id: number;
  company_name: string;
  title: string;
  location: string | null;
  job_url: string | null;
  jd_text: string | null;
  salary_range: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Stats {
  total_jobs: number;
  total_applied: number;
  total_interview: number;
  total_offer: number;
  total_rejected: number;
}

export interface User {
  id: number;
  email: string;
  created_at: string;
}

// ==================== 认证 API ====================

export async function register(email: string, password: string) {
  return apiPost("/auth/register", { email, password });
}

export async function login(email: string, password: string) {
  const data = await apiPost("/auth/login", { email, password });
  saveToken(data.access_token);
  return data;
}

export async function getMe(): Promise<User> {
  return apiGet("/auth/me");
}

// ==================== 岗位 API ====================

export async function createJob(data: {
  company_name: string;
  title: string;
  location?: string;
  job_url?: string;
  jd_text?: string;
  salary_range?: string;
  status?: string;
}): Promise<Job> {
  return apiPost("/jobs", data);
}

export async function getJobs(): Promise<Job[]> {
  return apiGet("/jobs");
}

export async function getJob(id: number): Promise<Job> {
  return apiGet(`/jobs/${id}`);
}

export async function updateJob(id: number, data: object): Promise<Job> {
  return apiPut(`/jobs/${id}`, data);
}

export async function deleteJob(id: number) {
  return apiDelete(`/jobs/${id}`);
}

// ==================== 统计 API ====================

export async function getStats(): Promise<Stats> {
  return apiGet("/stats/summary");
}
