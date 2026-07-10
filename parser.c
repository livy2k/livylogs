#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <tlhelp32.h>
#include <process.h>
#include <ctype.h>
#include <time.h>

// Simple XOR key for basic string obfuscation
#define S_KEY 0x7A
#define BUFFER_SIZE 8192
#define MAX_PLAYERS 512

// XOR decrypter
void d(char* s) {
    if (!s) return;
    for(int i = 0; s[i] != '\0'; i++) s[i] ^= S_KEY;
}

// Obfuscated strings
unsigned char p_name[] = {0x26, 0x26, 0x54, 0x26, 0x54, 0x0A, 0x13, 0x0A, 0x1F, 0x26, 0x36, 0x13, 0x0C, 0x03, 0x36, 0x15, 0x1D, 0x03, 0x2A, 0x13, 0x0A, 0x1F, 0x00}; // \\.\pipe\LivyLogsPipe
unsigned char s_python_cmd[] = {0x1a, 0x13, 0x0e, 0x12, 0x15, 0x14, 0x5a, 0x16, 0x13, 0x0c, 0x03, 0x16, 0x15, 0x1d, 0x0d, 0x54, 0x0a, 0x03, 0x00}; // python livylogs.py

unsigned char s_swgclient[] = {0x29, 0xd, 0x1d, 0x39, 0x16, 0x13, 0x1f, 0x14, 0xe, 0x00};
unsigned char s_star_wars_galaxies[] = {0x29, 0xe, 0x1b, 0x8, 0x5a, 0x2d, 0x1b, 0x8, 0x9, 0x5a, 0x3d, 0x1b, 0x16, 0x1b, 0x2, 0x13, 0x1f, 0x9, 0x00};
unsigned char s_combat_log_analyzer[] = {0x39, 0x15, 0x17, 0x18, 0x1b, 0xe, 0x5a, 0x36, 0x15, 0x1d, 0x5a, 0x3b, 0x14, 0x1b, 0x16, 0x3, 0x0, 0x1f, 0x8, 0x00};
unsigned char s_damage_meter[] = {0x3e, 0x1b, 0x17, 0x1b, 0x1d, 0x1f, 0x5a, 0x37, 0x1f, 0xe, 0x1f, 0x8, 0x00};
unsigned char s_leaderboard[] = {0x36, 0x1f, 0x1b, 0x1e, 0x1f, 0x8, 0x18, 0x15, 0x1b, 0x8, 0x1e, 0x00};
unsigned char s_skimmers[] = {0x29, 0x11, 0x13, 0x17, 0x17, 0x1f, 0x8, 0x9, 0x00};
unsigned char s_details[] = {0x3e, 0x1f, 0xe, 0x1b, 0x13, 0x16, 0x9, 0x00};
unsigned char s_options[] = {0x35, 0xa, 0xe, 0x13, 0x15, 0x14, 0x9, 0x00};
unsigned char s_alexa[] = {0x3b, 0x16, 0x1f, 0x2, 0x1b, 0x00};
unsigned char s_livylogs_exe[] = {0x36, 0x13, 0xc, 0x3, 0x16, 0x15, 0x1d, 0x9, 0x54, 0x1f, 0x2, 0x1f, 0x00};
unsigned char s_parser_exe[] = {0xa, 0x1b, 0x8, 0x9, 0x1f, 0x8, 0x54, 0x1f, 0x2, 0x1f, 0x00};
unsigned char s_armor_prevented[] = {0x1b, 0x8, 0x17, 0x15, 0x8, 0x5a, 0xa, 0x8, 0x1f, 0xc, 0x1f, 0x14, 0xe, 0x1f, 0x1e, 0x00};
unsigned char s_looted[] = {0x16, 0x15, 0x15, 0xe, 0x1f, 0x1e, 0x00};
unsigned char s_from[] = {0x1c, 0x8, 0x15, 0x17, 0x00};
unsigned char s_has_died[] = {0x12, 0x1b, 0x9, 0x5a, 0x1e, 0x13, 0x1f, 0x1e, 0x00};
unsigned char s_armor_reduction[] = {0x1b, 0x8, 0x17, 0x15, 0x8, 0x25, 0x8, 0x1f, 0x1e, 0xf, 0x19, 0xe, 0x13, 0x15, 0x14, 0x00};
unsigned char s_loot[] = {0x16, 0x15, 0x15, 0xe, 0x00};
unsigned char s_activity[] = {0x1b, 0x19, 0xe, 0x13, 0xc, 0x13, 0xe, 0x3, 0x00};
unsigned char s_healing[] = {0x12, 0x1f, 0x1b, 0x16, 0x13, 0x14, 0x1d, 0x00};
unsigned char s_dealt[] = {0x1e, 0x1f, 0x1b, 0x16, 0xe, 0x00};
unsigned char s_taken[] = {0xe, 0x1b, 0x11, 0x1f, 0x14, 0x00};
unsigned char s_other_dealt[] = {0x15, 0xe, 0x12, 0x1f, 0x8, 0x25, 0x1e, 0x1f, 0x1b, 0x16, 0xe, 0x00};
unsigned char s_died[] = {0x1e, 0x13, 0x1f, 0x1e, 0x00};
unsigned char s_for[] = {0x1c, 0x15, 0x8, 0x00};
unsigned char s_on[] = {0x15, 0x14, 0x00};
unsigned char s_to[] = {0xe, 0x15, 0x00};
unsigned char s_you[] = {0x3, 0x15, 0xf, 0x00};

// State structures
typedef struct {
    char name[128];
    double damage;
    double healing;
    double taken;
    int hits;
    int misses;
    int avoided;
    int aoe_hits;
    int loot_count;
    time_t last_hit;
} PlayerStats;

PlayerStats g_players[MAX_PLAYERS];
int g_player_count = 0;

HWND target_hwnd = NULL;
DWORD python_pid = 0;

void a_o_t(BOOL s_s) {
    char s_cla[32];
    strcpy(s_cla, (char*)s_combat_log_analyzer); d(s_cla);
    HWND h_cla = FindWindowA(NULL, s_cla);
    if (h_cla) {
        if (s_s) SetWindowPos(h_cla, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        else SetWindowPos(h_cla, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    }
    
    unsigned char* pop_list[] = {s_damage_meter, s_leaderboard, s_skimmers, s_details, s_options, s_alexa};
    for (int i = 0; i < 6; i++) {
        char n_b[32];
        strcpy(n_b, (char*)pop_list[i]); d(n_b);
        HWND h = FindWindowA(NULL, n_b);
        if (h && IsWindowVisible(h)) {
            if (s_s) SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
            else SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        }
    }
}

// Internal helpers
PlayerStats* get_player(const char* name) {
    if (!name || !*name) return NULL;
    char n[128];
    strncpy(n, name, 127); n[127] = '\0';
    for(int i=0; i<g_player_count; i++) {
        if(_stricmp(g_players[i].name, n) == 0) return &g_players[i];
    }
    if(g_player_count < MAX_PLAYERS) {
        strncpy(g_players[g_player_count].name, n, 127);
        g_players[g_player_count].damage = 0;
        g_players[g_player_count].healing = 0;
        g_players[g_player_count].taken = 0;
        g_players[g_player_count].hits = 0;
        g_players[g_player_count].misses = 0;
        g_players[g_player_count].avoided = 0;
        g_players[g_player_count].aoe_hits = 0;
        g_players[g_player_count].loot_count = 0;
        g_players[g_player_count].last_hit = 0;
        return &g_players[g_player_count++];
    }
    return NULL;
}

BOOL CALLBACK e_w_p(HWND h, LPARAM l) {
    if (IsWindowVisible(h)) {
        wchar_t b[256];
        GetWindowTextW(h, b, 256);
        char s1[32], s2[32];
        strcpy(s1, (char*)s_swgclient); d(s1);
        strcpy(s2, (char*)s_star_wars_galaxies); d(s2);
        
        wchar_t w1[32], w2[32];
        MultiByteToWideChar(CP_ACP, 0, s1, -1, w1, 32);
        MultiByteToWideChar(CP_ACP, 0, s2, -1, w2, 32);

        if (wcsstr(b, w1) || wcsstr(b, w2)) {
            target_hwnd = h;
            return FALSE;
        }
    }
    return TRUE;
}

void u_v() {
    if (!target_hwnd || !IsWindow(target_hwnd)) {
        EnumWindows(e_w_p, 0);
    }

    HWND fg = GetForegroundWindow();
    DWORD f_p = 0;
    if (fg) GetWindowThreadProcessId(fg, &f_p);

    BOOL o = (f_p != 0 && (f_p == GetCurrentProcessId() || f_p == python_pid));
    if (!o && target_hwnd) {
        DWORD t_p = 0;
        GetWindowThreadProcessId(target_hwnd, &t_p);
        if (f_p != 0 && f_p == t_p) o = TRUE;
        
        // Title-based fallback for focus detection
        if (!o && fg) {
            wchar_t cur_t[256];
            GetWindowTextW(fg, cur_t, 256);
            char s1[32], s2[32];
            strcpy(s1, (char*)s_swgclient); d(s1);
            strcpy(s2, (char*)s_star_wars_galaxies); d(s2);
            wchar_t w1[32], w2[32];
            MultiByteToWideChar(CP_ACP, 0, s1, -1, w1, 32);
            MultiByteToWideChar(CP_ACP, 0, s2, -1, w2, 32);
            if (wcsstr(cur_t, w1) || wcsstr(cur_t, w2)) o = TRUE;
        }

        // Robust check: if foreground window is owned by game or python, it's 'o'
        if (!o && fg) {
            HWND owner = GetWindow(fg, GW_OWNER);
            int depth = 0;
            while (owner && depth < 10) {
                DWORD opid = 0;
                GetWindowThreadProcessId(owner, &opid);
                if (opid != 0 && (opid == t_p || opid == python_pid || opid == GetCurrentProcessId())) {
                    o = TRUE;
                    break;
                }
                owner = GetWindow(owner, GW_OWNER);
                depth++;
            }
        }
        
        if (!o && t_p != 0 && f_p != 0 && f_p == t_p) o = TRUE;
    }

    // NEW: Aggressively HIDE TtkMonitorWindow
    if (fg) {
        char cls[256];
        GetClassNameA(fg, cls, 256);
        if (strstr(cls, "TtkMonitorWindow")) {
            ShowWindow(fg, SW_HIDE);
        }
    }

    // Safety check for TtkMonitorWindow - if this is the foreground, DON'T hide
    if (!o && fg) {
        char cls[256];
        GetClassNameA(fg, cls, 256);
        if (strstr(cls, "TtkMonitorWindow")) o = TRUE;
    }

    DWORD t_pid = 0;
    wchar_t fg_title[256] = L"";
    if (target_hwnd) GetWindowThreadProcessId(target_hwnd, &t_pid);
    if (fg) GetWindowTextW(fg, fg_title, 256);

    BOOL m = (target_hwnd != NULL) ? IsIconic(target_hwnd) : FALSE;
    BOOL s_s = (o || GetAsyncKeyState(VK_MENU)) && !m;
    
    // Safety check: if target_hwnd is lost, but was recently found, keep it
    static HWND last_valid_target = NULL;
    if (target_hwnd) last_valid_target = target_hwnd;
    
    // Grace period for hiding - increased for better stability
    static DWORD last_show_time = 0;
    if (s_s) last_show_time = GetTickCount();
    if (!s_s && (GetTickCount() - last_show_time < 2000)) s_s = TRUE;

    // Additional check: If the foreground window title is empty OR common system/utility titles
    // don't hide yet. Added "Discord", "Avast", and "NVIDIA" to the list.
    // BUT we only do this for the purpose of KEEPING windows, not for TOPMOST status.
    // So we'll refine this later.
    if (!s_s) {
        if (wcslen(fg_title) == 0) s_s = TRUE;
        else if (wcsstr(fg_title, L"Search") != NULL) s_s = TRUE;
        else if (wcsstr(fg_title, L"Start") != NULL) s_s = TRUE;
        else if (wcsstr(fg_title, L"Task Manager") != NULL) s_s = TRUE;
        else if (wcsstr(fg_title, L"Discord") != NULL) s_s = TRUE;
        else if (wcsstr(fg_title, L"Avast") != NULL) s_s = TRUE;
        else if (wcsstr(fg_title, L"NVIDIA") != NULL) s_s = TRUE;
        else if (wcsstr(fg_title, L"Steam") != NULL) s_s = TRUE;
    }

    // Force show if game window is detected but we are in-game (o is true)
    // even if IsIconic is somehow true (might happen in some borderless modes)
    if (o) s_s = TRUE;

    // If we haven't found the game window yet, don't hide the overlay
    if (!target_hwnd && !last_valid_target) s_s = TRUE;
    
    // Safety: If game is found but we lost focus tracking for some reason, 
    // allow force-showing with ALT
    if (GetAsyncKeyState(VK_MENU)) s_s = TRUE;

    // Let's add one more thing: if we fail to find target_hwnd, keep it shown.
    if (!target_hwnd) s_s = TRUE;

        // ACTUAL VISIBILITY vs TOPMOST logic
        // We want the windows to only be TOPMOST if 'o' is true (game or app has focus)
        // or if we are in the grace period but the game is actually the foreground.
        BOOL t_m = o; // t_m = Topmost Mode
        if (!t_m && s_s && target_hwnd) {
            // If we are in grace period and game is still foreground (but maybe f_p != t_p due to popups)
            if (f_p == t_pid) t_m = TRUE;
        }
        
    // Safety check: If the foreground window is "Start" or belongs to Explorer.exe, 
    // treat it as a "safe" window that keeps our current visibility state.
    if (!t_m && fg) {
        char cls[256];
        GetClassNameA(fg, cls, 256);
        if (strstr(cls, "Windows.UI.Core.CoreWindow") || strstr(cls, "Explorer") || 
            strstr(cls, "TrayNotifyWnd") || strstr(cls, "Launcher") || strstr(cls, "Shell_TrayWnd") ||
            strstr(cls, "DV2ControlHost") || strstr(cls, "BaseBar") || strstr(cls, "NotifyIconOverflowWindow")) {
            // Keep visibility but don't force topmost
            s_s = TRUE;
        }
    }

    // FORCED OVERRIDE: If game is in foreground, WE ARE TOPMOST. Period.
    if (target_hwnd && f_p == t_pid) {
        s_s = TRUE;
        t_m = TRUE;
    }

    static DWORD last_log = 0;
    if (GetTickCount() - last_log > 1000) {
        FILE* f = fopen("engine_debug.txt", "a");
        if (f) {
            char title_mb[256];
            WideCharToMultiByte(CP_ACP, 0, fg_title, -1, title_mb, 256, NULL, NULL);
            fprintf(f, "target: %p, t_pid: %lu, fg: %p (%s), fg_pid: %lu, py_pid: %lu, c_pid: %lu, o: %d, m: %d, s_s: %d, v_t: %d\n", 
                    target_hwnd, t_pid, fg, title_mb, f_p, python_pid, GetCurrentProcessId(), o, m, s_s, (target_hwnd && !m));
            fclose(f);
        }
        last_log = GetTickCount();
    }

    static BOOL last_s_s = -1;
    if (s_s != last_s_s) {
        last_s_s = s_s;
    }

    // Use partial matching or class name for more reliable window finding
    char s_cla[32];
    strcpy(s_cla, (char*)s_combat_log_analyzer); d(s_cla);
    HWND p_h = NULL;
    
    // NEW: Debug info for finding p_h
    static DWORD last_ph_debug = 0;

    // Attempt to find window by PID first as it's most reliable
    if (python_pid) {
        HWND h = GetTopWindow(NULL);
        while (h) {
            DWORD pid;
            GetWindowThreadProcessId(h, &pid);
            if (pid == python_pid) {
                // Check if it's a real window (has title or common class)
                char cls[256];
                GetClassNameA(h, cls, 256);
                if (strstr(cls, "TkTopLevel") || strstr(cls, "TkChild") || GetWindowTextLengthA(h) > 0) {
                    if (GetTickCount() - last_ph_debug > 2000) {
                        FILE* f = fopen("engine_debug.txt", "a");
                        if (f) {
                            char title[256];
                            GetWindowTextA(h, title, 256);
                            fprintf(f, "FOUND PY_WINDOW: HWND: %p, PID: %lu, Title: %s, Class: %s\n", h, pid, title, cls);
                            fclose(f);
                        }
                    }
                    p_h = h;
                    break;
                }
            }
            h = GetNextWindow(h, GW_HWNDNEXT);
        }
    }
    if (GetTickCount() - last_ph_debug > 2000) last_ph_debug = GetTickCount();

    if (!p_h) p_h = FindWindowA(NULL, s_cla);
    if (!p_h) p_h = FindWindowA("TkTopLevel", s_cla);
    if (!p_h) p_h = FindWindowA("TkChild", s_cla);
    if (!p_h) p_h = FindWindowA("TkTopLevel", "Combat Log Analyzer");
    
    // Robust search: if still not found, search windows belonging to the python process
    if (!p_h && python_pid) {
        HWND h = GetTopWindow(NULL);
        while (h) {
            DWORD pid;
            GetWindowThreadProcessId(h, &pid);
            if (pid == python_pid) {
                char title[256];
                GetWindowTextA(h, title, 256);
                if (strstr(title, s_cla) || strstr(title, "Combat Log Analyzer") || strstr(title, "LivyLogs")) {
                    p_h = h;
                    break;
                }
            }
            h = GetNextWindow(h, GW_HWNDNEXT);
        }
    }
    
    if (p_h) {
        // ALWAYS keep main window visible as requested
        if (IsIconic(p_h)) ShowWindow(p_h, SW_RESTORE);
        
        // FORCED PERSISTENCE for main window - Using SW_SHOW to ensure it doesn't get stuck hidden
        ShowWindow(p_h, SW_SHOWNA);
        
        // Ensure it doesn't stay topmost if we are NOT in topmost mode
        // This fixes the issue where clicking it while on top (of SWG) makes it stay on top (of Start menu)
        if (t_m) {
            // Use HWND_TOPMOST when game/app has focus
            SetWindowPos(p_h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
            // Force it to the top one more time
            BringWindowToTop(p_h);
        } else {
            // Remove TOPMOST when focus lost (ALT-TAB / Start Menu) but keep visible
            SetWindowPos(p_h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
        }
    }

    unsigned char* p_l_v[] = {s_damage_meter, s_leaderboard, s_skimmers, s_details, s_options, s_alexa};
    for (int i = 0; i < 6; i++) {
        char n_b[32];
        strcpy(n_b, (char*)p_l_v[i]); d(n_b);
        HWND h = FindWindowA(NULL, n_b);
        if (!h) h = FindWindowA("TkTopLevel", n_b);
        if (!h) h = FindWindowA("TkChild", n_b);
        
        // Robust search for popouts
        if (!h && python_pid) {
            HWND h2 = GetTopWindow(NULL);
            while (h2) {
                DWORD pid;
                GetWindowThreadProcessId(h2, &pid);
                if (pid == python_pid) {
                    char title[256];
                    GetWindowTextA(h2, title, 256);
                    if (strstr(title, n_b)) {
                        h = h2;
                        break;
                    }
                }
                h2 = GetNextWindow(h2, GW_HWNDNEXT);
            }
        }
        
        if (h) {
            if (s_s) {
                if (IsIconic(h)) ShowWindow(h, SW_RESTORE);
                ShowWindow(h, SW_SHOWNOACTIVATE);
                if (t_m) SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW);
                else SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
            } else {
                ShowWindow(h, SW_HIDE);
                SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_HIDEWINDOW);
            }
        }
    }

    a_o_t(t_m);
}

void c_o() {
    HANDLE h_s = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (h_s == INVALID_HANDLE_VALUE) return;
    PROCESSENTRY32 p_e;
    p_e.dwSize = sizeof(PROCESSENTRY32);
    DWORD m_p = GetCurrentProcessId();
    
    char e1[32], e2[32];
    strcpy(e1, (char*)s_livylogs_exe); d(e1);
    strcpy(e2, (char*)s_parser_exe); d(e2);

    if (Process32First(h_s, &p_e)) {
        do {
            if ((_stricmp(p_e.szExeFile, e1) == 0 || _stricmp(p_e.szExeFile, e2) == 0) && p_e.th32ProcessID != m_p) {
                HANDLE h_p = OpenProcess(PROCESS_TERMINATE, FALSE, p_e.th32ProcessID);
                if (h_p) {
                    TerminateProcess(h_p, 0);
                    CloseHandle(h_p);
                }
            }
        } while (Process32Next(h_s, &p_e));
    }
    CloseHandle(h_s);
}

void e_j(const char* s, char* d_p) {
    while (*s) {
        if (*s == '\"' || *s == '\\') *d_p++ = '\\';
        *d_p++ = *s++;
    }
    *d_p = '\0';
}

void s_e(HANDLE h, const char* t, const char* s_c, const char* t_g, double d_m, double h_l, const char* a, const char* i_t, int m_t) {
    char j[BUFFER_SIZE];
    char e_s[256], e_t[256], e_a[256], e_i[256];
    e_j(s_c, e_s);
    e_j(t_g, e_t);
    e_j(a, e_a);
    e_j(i_t, e_i);

    sprintf(j, "{\"type\": \"%s\", \"source\": \"%s\", \"target\": \"%s\", \"damage\": %.2f, \"healing\": %.2f, \"ability\": \"%s\", \"item\": \"%s\", \"is_mitigated\": %s}\n",
            t, e_s, e_t, d_m, h_l, e_a, e_i, m_t ? "true" : "false");
    
    DWORD w_b;
    WriteFile(h, j, (DWORD)strlen(j), &w_b, NULL);
}

void s_s(HANDLE h) {
    for(int i=0; i<g_player_count; i++) {
        char j[BUFFER_SIZE];
        char e_n[256];
        e_j(g_players[i].name, e_n);
        sprintf(j, "{\"type\": \"stats\", \"name\": \"%s\", \"damage\": %.2f, \"healing\": %.2f, \"taken\": %.2f, \"hits\": %d, \"misses\": %d, \"avoided\": %d, \"aoe\": %d, \"loot\": %d}\n",
                e_n, g_players[i].damage, g_players[i].healing, g_players[i].taken, g_players[i].hits, g_players[i].misses, g_players[i].avoided, g_players[i].aoe_hits, g_players[i].loot_count);
        DWORD w_b;
        WriteFile(h, j, (DWORD)strlen(j), &w_b, NULL);
    }
}

char* s_i_s(const char* s1, const char* s2) {
    if (!*s2) return (char*)s1;
    for (; *s1; ++s1) {
        if (tolower(*s1) == tolower(*s2)) {
            const char *h_p, *n_p;
            for (h_p = s1, n_p = s2; *h_p && *n_p; ++h_p, ++n_p) {
                if (tolower(*h_p) != tolower(*n_p)) break;
            }
            if (!*n_p) return (char*)s1;
        }
    }
    return NULL;
}

void p_l(HANDLE h, char* l) {
    if (!l || strlen(l) < 10) return;

    char* clean = l;
    if (l[0] == '[') {
        char* end_bracket = strchr(l, ']');
        if (end_bracket) clean = end_bracket + 1;
    }
    while(*clean == ' ') clean++;
    if (isdigit(clean[0]) && isdigit(clean[1]) && clean[2] == ':') {
        clean += 9;
    }
    while(*clean == ' ') clean++;

    char lower[BUFFER_SIZE];
    for(int i=0; clean[i]; i++) lower[i] = tolower(clean[i]);
    lower[strlen(clean)] = '\0';

    char s_ap[32], s_lt[32], s_fr[32], s_hd[32], s_ar[32], s_l_key[32], s_ac[32], s_he[32], s_de[32], s_tk[32], s_od[32], s_di[32], s_f[32], s_o[32], s_t[32], s_y[32];

    // Armor prevented
    strcpy(s_ap, (char*)s_armor_prevented); d(s_ap);
    if (strstr(lower, s_ap)) {
        char* p = s_i_s(clean, s_ap);
        if (p) {
            double red = 0;
            if (sscanf(p + 16, "%lf", &red) == 1) {
                strcpy(s_ar, (char*)s_armor_reduction); d(s_ar);
                s_e(h, s_ar, "", "", red, 0, "", "", 0);
            }
        }
        return;
    }

    // Loot
    strcpy(s_lt, (char*)s_looted); d(s_lt);
    if (strstr(lower, s_lt)) {
        char* p_loot = s_i_s(clean, s_lt);
        if (p_loot) {
            char name[128] = "Unknown", item[256] = "Unknown";
            int n_len = p_loot - clean;
            if (n_len > 127) n_len = 127;
            strncpy(name, clean, n_len); name[n_len] = '\0';
            strcpy(s_fr, (char*)s_from); d(s_fr);
            char* p_from = s_i_s(p_loot, s_fr);
            if (p_from) {
                int i_len = p_from - (p_loot + 7);
                if (i_len > 255) i_len = 255;
                if (i_len > 0) {
                    strncpy(item, p_loot + 7, i_len); item[i_len] = '\0';
                    strcpy(s_l_key, (char*)s_loot); d(s_l_key);
                    s_e(h, s_l_key, name, "Unknown", 0, 0, "", item, 0);
                    PlayerStats* ps = get_player(name);
                    if(ps) ps->loot_count++;
                    return;
                }
            }
        }
    }

    // Death
    strcpy(s_hd, (char*)s_has_died); d(s_hd);
    if (strstr(lower, s_hd)) {
        char* p_died = s_i_s(clean, s_hd);
        if (p_died) {
            char name[128] = "Unknown";
            int n_len = p_died - clean;
            if (n_len > 127) n_len = 127;
            strncpy(name, clean, n_len); name[n_len] = '\0';
            strcpy(s_ac, (char*)s_activity); d(s_ac);
            strcpy(s_di, (char*)s_died); d(s_di);
            s_e(h, s_ac, name, "Unknown", 0, 0, "", s_di, 0);
            return;
        }
    }

    // Combat
    const char* actions[] = {"uses", "use", "attacks", "attack", "deals", "deal", "heals", "heal", "hits", "hit"};
    const char* mits[] = {"evades", "evaded", "dodges", "parries", "blocks it", "counterattacks"};
    
    int is_mit = 0;
    for(int i=0; i<6; i++) { if(strstr(lower, mits[i])) { is_mit = 1; break; } }

    for(int i=0; i<10; i++) {
        char* p_act = s_i_s(clean, actions[i]);
        if (p_act) {
            char source[128] = "Unknown", target[128] = "Unknown", ability[128] = "";
            double amount = 0;

            int s_len = p_act - clean;
            if (s_len > 127) s_len = 127;
            strncpy(source, clean, s_len); source[s_len] = '\0';
            while(s_len > 0 && source[s_len-1] == ' ') source[--s_len] = '\0';

            strcpy(s_f, (char*)s_for); d(s_f);
            char* p_for = s_i_s(p_act, s_f);
            if (p_for) {
                if (sscanf(p_for + 4, "%lf", &amount) == 1) {
                    strcpy(s_o, (char*)s_on); d(s_o);
                    strcpy(s_t, (char*)s_to); d(s_t);
                    char* p_on = s_i_s(p_act, s_o);
                    if (!p_on) p_on = s_i_s(p_act, s_t);
                    
                    if (p_on && p_on < p_for) {
                        int a_len = p_on - (p_act + strlen(actions[i]));
                        if (a_len > 0) {
                            if (a_len > 127) a_len = 127;
                            strncpy(ability, p_act + strlen(actions[i]), a_len); ability[a_len] = '\0';
                        }
                        int t_len = p_for - (p_on + 3);
                        if (t_len > 0) {
                            if (t_len > 127) t_len = 127;
                            strncpy(target, p_on + 3, t_len); target[t_len] = '\0';
                        }
                    } else {
                        int t_len = p_for - (p_act + strlen(actions[i]));
                        if (t_len > 0) {
                            if (t_len > 127) t_len = 127;
                            strncpy(target, p_act + strlen(actions[i]), t_len); target[t_len] = '\0';
                        }
                    }

                    while(strlen(source)>0 && source[0]==' ') memmove(source, source+1, strlen(source));
                    while(strlen(target)>0 && target[0]==' ') memmove(target, target+1, strlen(target));
                    while(strlen(ability)>0 && ability[0]==' ') memmove(ability, ability+1, strlen(ability));
                    char* end;
                    end = source + strlen(source) - 1; while(end >= source && isspace(*end)) *end-- = '\0';
                    end = target + strlen(target) - 1; while(end >= target && (isspace(*end) || *end == '!')) *end-- = '\0';
                    end = ability + strlen(ability) - 1; while(end >= ability && isspace(*end)) *end-- = '\0';

                    PlayerStats* ps_src = get_player(source);
                    PlayerStats* ps_tgt = get_player(target);

                    if (strstr(actions[i], "heal")) {
                        strcpy(s_he, (char*)s_healing); d(s_he);
                        s_e(h, s_he, source, target, 0, amount, ability, "", 0);
                        if(ps_src) ps_src->healing += amount;
                    } else {
                        strcpy(s_tk, (char*)s_taken); d(s_tk);
                        strcpy(s_de, (char*)s_dealt); d(s_de);
                        strcpy(s_od, (char*)s_other_dealt); d(s_od);
                        strcpy(s_y, (char*)s_you); d(s_y);

                        char* type = s_od;
                        if (_stricmp(source, s_y) == 0) type = s_de;
                        else if (_stricmp(target, s_y) == 0) type = s_tk;
                        s_e(h, type, source, target, is_mit ? 0 : amount, 0, ability, "", is_mit);
                        
                        if(ps_src) {
                            if(is_mit) ps_src->misses++;
                            else {
                                ps_src->damage += amount;
                                ps_src->hits++;
                                time_t now = time(NULL);
                                if(now == ps_src->last_hit) ps_src->aoe_hits++;
                                ps_src->last_hit = now;
                            }
                        }
                        if(ps_tgt) {
                            if(is_mit) ps_tgt->avoided++;
                            else ps_tgt->taken += amount;
                        }
                    }
                    return;
                }
            }
        }
    }
}

void e_t(void* arg) {
    char* l_p = (char*)arg;
    char d_pn[64];
    strcpy(d_pn, (char*)p_name); d(d_pn);

    HANDLE hp = CreateNamedPipe(d_pn, PIPE_ACCESS_OUTBOUND, PIPE_TYPE_BYTE | PIPE_WAIT, 1, 0, 0, 0, NULL);
    if (hp == INVALID_HANDLE_VALUE) return;

    ConnectNamedPipe(hp, NULL);

    HANDLE hf = CreateFile(l_p, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hf == INVALID_HANDLE_VALUE) { CloseHandle(hp); return; }

    SetFilePointer(hf, 0, NULL, FILE_END);

    char b_buf[BUFFER_SIZE];
    DWORD r_b;
    char l_o[BUFFER_SIZE] = "";
    time_t last_sync = time(NULL);

    while (1) {
        if (ReadFile(hf, b_buf, BUFFER_SIZE - 2, &r_b, NULL) && r_b > 0) {
            b_buf[r_b] = '\0';
            char t_buf[BUFFER_SIZE * 2];
            strcpy(t_buf, l_o);
            strcat(t_buf, b_buf);
            
            char* line = t_buf;
            char* next;
            while ((next = strchr(line, '\n')) != NULL) {
                *next = '\0';
                if (next > line && *(next-1) == '\r') *(next-1) = '\0';
                p_l(hp, line);
                line = next + 1;
            }
            strcpy(l_o, line);
        } else {
            Sleep(100);
        }
        
        time_t now = time(NULL);
        if(now - last_sync >= 1) {
            s_s(hp);
            last_sync = now;
        }
    }
    CloseHandle(hf);
    CloseHandle(hp);
}

int main(int a, char** v) {
    c_o();
    
    char p_c[128];
    strcpy(p_c, (char*)s_python_cmd); d(p_c);
    
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    // Check if livylogs.py exists
    FILE* f_chk = fopen("livylogs.py", "r");
    if (f_chk) {
        fclose(f_chk);
    } else {
        FILE* f_err = fopen("engine_debug.txt", "a");
        if (f_err) {
            fprintf(f_err, "ERROR: livylogs.py NOT FOUND in current directory!\n");
            fclose(f_err);
        }
    }

    // Use absolute path for python for maximum reliability and speed
    char p_abs[256];
    sprintf(p_abs, "\"C:\\Users\\LivyC\\AppData\\Local\\Programs\\Python\\Python312\\python.exe\" livylogs.py");

    if (!CreateProcess(NULL, p_abs, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        FILE* f_err = fopen("engine_debug.txt", "a");
        if (f_err) {
            fprintf(f_err, "ERROR: Failed to launch Python (cmd: %s), error code: %lu\n", p_abs, GetLastError());
            fclose(f_err);
        }
        // Fallback to ShellExecute if absolute path fails
        ShellExecuteA(NULL, "open", "livylogs.py", NULL, NULL, SW_HIDE);
    } else {
        python_pid = pi.dwProcessId;
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    if (a >= 2) {
        _beginthread(e_t, 0, v[1]);
    }

    DWORD start_time = GetTickCount();

    while (1) {
        // Wait 1 second before managing windows to allow Python UI to stabilize
        if (GetTickCount() - start_time > 1000) {
            u_v();
        }
        Sleep(250);
    }
    return 0;
}
