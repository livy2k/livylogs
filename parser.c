#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <tlhelp32.h>
#include <process.h>
#include <ctype.h>

// Simple XOR key for basic string obfuscation
#define S_KEY 0x7A
#define BUFFER_SIZE 8192

// XOR decrypter
void d(char* s) {
    for(int i = 0; s[i] != '\0'; i++) s[i] ^= S_KEY;
}

// Obfuscated strings
unsigned char p_name[] = {0x26, 0x26, 0x54, 0x26, 0x54, 0x0A, 0x13, 0x0A, 0x1F, 0x26, 0x36, 0x13, 0x0C, 0x03, 0x36, 0x15, 0x1D, 0x03, 0x2A, 0x13, 0x0A, 0x1F, 0x00}; // \\.\pipe\LivyLogsPipe
unsigned char s_python_cmd[] = {0x0A, 0x03, 0x0E, 0x12, 0x15, 0x14, 0x5A, 0x16, 0x13, 0x0C, 0x03, 0x16, 0x15, 0x1D, 0x0D, 0x54, 0x0A, 0x03, 0x00}; // python livylogs.py

HWND target_hwnd = NULL;
DWORD python_pid = 0;

BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam) {
    if (IsWindowVisible(hwnd)) {
        wchar_t buf[256];
        GetWindowTextW(hwnd, buf, 256);
        if (wcsstr(buf, L"SwgClient") || wcsstr(buf, L"Star Wars Galaxies")) {
            target_hwnd = hwnd;
            return FALSE;
        }
    }
    return TRUE;
}

void update_visibility() {
    if (!target_hwnd || !IsWindow(target_hwnd)) {
        EnumWindows(EnumWindowsProc, 0);
    }

    HWND fg = GetForegroundWindow();
    DWORD fg_pid;
    GetWindowThreadProcessId(fg, &fg_pid);

    BOOL ours = (fg_pid == GetCurrentProcessId() || fg_pid == python_pid);
    if (!ours && target_hwnd) {
        DWORD target_pid;
        GetWindowThreadProcessId(target_hwnd, &target_pid);
        if (fg_pid == target_pid) ours = TRUE;
    }

    BOOL minimized = IsIconic(target_hwnd);
    BOOL should_show = (ours || GetAsyncKeyState(VK_MENU)) && !minimized;

    HWND python_hwnd = FindWindowA(NULL, "Combat Log Analyzer");
    if (python_hwnd) {
        if (should_show) {
            ShowWindow(python_hwnd, SW_SHOWNOACTIVATE);
            SetWindowPos(python_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        } else {
            ShowWindow(python_hwnd, SW_HIDE);
        }
    }

    const char* popouts[] = {"Damage Meter", "Leaderboard", "Skimmers", "Details", "Options", "Alexa"};
    for (int i = 0; i < 6; i++) {
        HWND h = FindWindowA(NULL, popouts[i]);
        if (h) {
            if (should_show) {
                ShowWindow(h, SW_SHOWNOACTIVATE);
                SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
            } else {
                ShowWindow(h, SW_HIDE);
            }
        }
    }
}

void cleanup_orphans() {
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) return;
    PROCESSENTRY32 pe;
    pe.dwSize = sizeof(PROCESSENTRY32);
    DWORD myPid = GetCurrentProcessId();
    if (Process32First(hSnap, &pe)) {
        do {
            if ((_stricmp(pe.szExeFile, "Livylogs.exe") == 0 || _stricmp(pe.szExeFile, "parser.exe") == 0) && pe.th32ProcessID != myPid) {
                HANDLE hProc = OpenProcess(PROCESS_TERMINATE, FALSE, pe.th32ProcessID);
                if (hProc) {
                    TerminateProcess(hProc, 0);
                    CloseHandle(hProc);
                }
            }
        } while (Process32Next(hSnap, &pe));
    }
    CloseHandle(hSnap);
}

void escape_json(const char* src, char* dst) {
    while (*src) {
        if (*src == '\"' || *src == '\\') *dst++ = '\\';
        *dst++ = *src++;
    }
    *dst = '\0';
}

void send_event(HANDLE h, const char* type, const char* source, const char* target, double damage, double healing, const char* ability, const char* item, int mitigated) {
    char j[BUFFER_SIZE];
    char e_src[256], e_tgt[256], e_abi[256], e_itm[256];
    escape_json(source, e_src);
    escape_json(target, e_tgt);
    escape_json(ability, e_abi);
    escape_json(item, e_itm);

    sprintf(j, "{\"type\": \"%s\", \"source\": \"%s\", \"target\": \"%s\", \"damage\": %.2f, \"healing\": %.2f, \"ability\": \"%s\", \"item\": \"%s\", \"is_mitigated\": %s}\n",
            type, e_src, e_tgt, damage, healing, e_abi, e_itm, mitigated ? "true" : "false");
    
    DWORD w;
    WriteFile(h, j, (DWORD)strlen(j), &w, NULL);
}

char* stristr(const char* str1, const char* str2) {
    if (!*str2) return (char*)str1;
    for (; *str1; ++str1) {
        if (tolower(*str1) == tolower(*str2)) {
            const char *h, *n;
            for (h = str1, n = str2; *h && *n; ++h, ++n) {
                if (tolower(*h) != tolower(*n)) break;
            }
            if (!*n) return (char*)str1;
        }
    }
    return NULL;
}

// Global state for armor prevented logic
double last_taken_damage = 0;
char last_taken_source[256] = "";

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

    // Armor prevented
    if (strstr(lower, "armor prevented")) {
        char* p = stristr(clean, "armor prevented");
        if (p) {
            double red = 0;
            if (sscanf(p + 16, "%lf", &red) == 1) {
                send_event(h, "armor_reduction", "", "", red, 0, "", "", 0);
            }
        }
        return;
    }

    // Loot
    if (strstr(lower, "looted")) {
        char* p_loot = stristr(clean, "looted");
        if (p_loot) {
            char name[128] = "Unknown", item[256] = "Unknown";
            int n_len = p_loot - clean;
            if (n_len > 127) n_len = 127;
            strncpy(name, clean, n_len); name[n_len] = '\0';
            char* p_from = stristr(p_loot, "from");
            if (p_from) {
                int i_len = p_from - (p_loot + 7);
                if (i_len > 255) i_len = 255;
                if (i_len > 0) {
                    strncpy(item, p_loot + 7, i_len); item[i_len] = '\0';
                    send_event(h, "loot", name, "Unknown", 0, 0, "", item, 0);
                    return;
                }
            }
        }
    }

    // Death
    if (strstr(lower, "has died")) {
        char* p_died = stristr(clean, "has died");
        if (p_died) {
            char name[128] = "Unknown";
            int n_len = p_died - clean;
            if (n_len > 127) n_len = 127;
            strncpy(name, clean, n_len); name[n_len] = '\0';
            send_event(h, "activity", name, "Unknown", 0, 0, "", "died", 0);
            return;
        }
    }

    // Combat
    const char* actions[] = {"uses", "use", "attacks", "attack", "deals", "deal", "heals", "heal", "hits", "hit"};
    const char* mits[] = {"evades", "evaded", "dodges", "parries", "blocks it", "counterattacks"};
    
    int is_mit = 0;
    for(int i=0; i<6; i++) { if(strstr(lower, mits[i])) { is_mit = 1; break; } }

    for(int i=0; i<10; i++) {
        char* p_act = stristr(clean, actions[i]);
        if (p_act) {
            char source[128] = "Unknown", target[128] = "Unknown", ability[128] = "";
            double amount = 0;

            int s_len = p_act - clean;
            if (s_len > 127) s_len = 127;
            strncpy(source, clean, s_len); source[s_len] = '\0';
            while(s_len > 0 && source[s_len-1] == ' ') source[--s_len] = '\0';

            char* p_for = stristr(p_act, "for");
            if (p_for) {
                if (sscanf(p_for + 4, "%lf", &amount) == 1) {
                    char* p_on = stristr(p_act, "on");
                    if (!p_on) p_on = stristr(p_act, "to");
                    
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

                    if (strstr(actions[i], "heal")) {
                        send_event(h, "healing", source, target, 0, amount, ability, "", 0);
                    } else {
                        const char* type = "other_dealt";
                        if (_stricmp(source, "you") == 0) type = "dealt";
                        else if (_stricmp(target, "you") == 0) type = "taken";
                        send_event(h, type, source, target, is_mit ? 0 : amount, 0, ability, "", is_mit);
                    }
                    return;
                }
            }
        }
    }
}

void engine_thread(void* arg) {
    char* log_path = (char*)arg;
    char d_pn[64];
    strcpy(d_pn, (char*)p_name); d(d_pn);

    HANDLE hp = CreateNamedPipe(d_pn, PIPE_ACCESS_OUTBOUND, PIPE_TYPE_BYTE | PIPE_WAIT, 1, 0, 0, 0, NULL);
    if (hp == INVALID_HANDLE_VALUE) return;

    ConnectNamedPipe(hp, NULL);

    HANDLE hf = CreateFile(log_path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hf == INVALID_HANDLE_VALUE) { CloseHandle(hp); return; }

    SetFilePointer(hf, 0, NULL, FILE_END);

    char b[BUFFER_SIZE];
    DWORD r;
    char leftover[BUFFER_SIZE] = "";

    while (1) {
        if (ReadFile(hf, b, BUFFER_SIZE - 2, &r, NULL) && r > 0) {
            b[r] = '\0';
            char temp[BUFFER_SIZE * 2];
            strcpy(temp, leftover);
            strcat(temp, b);
            
            char* line = temp;
            char* next;
            while ((next = strchr(line, '\n')) != NULL) {
                *next = '\0';
                if (next > line && *(next-1) == '\r') *(next-1) = '\0';
                p_l(hp, line);
                line = next + 1;
            }
            strcpy(leftover, line);
        } else {
            Sleep(100);
        }
    }
    CloseHandle(hf);
    CloseHandle(hp);
}

int main(int a, char** v) {
    cleanup_orphans();
    
    char python_cmd[128];
    strcpy(python_cmd, (char*)s_python_cmd); d(python_cmd);
    
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    if (CreateProcess(NULL, python_cmd, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        python_pid = pi.dwProcessId;
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    if (a >= 2) {
        _beginthread(engine_thread, 0, v[1]);
    }

    while (1) {
        update_visibility();
        Sleep(250);
    }
    return 0;
}
