#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Simple XOR key for basic string obfuscation
#define S_KEY 0x7A
#define BUFFER_SIZE 4096

// XOR decrypter to hide strings from static analysis/strings.exe
void d(char* s) {
    for(int i = 0; s[i] != '\0'; i++) s[i] ^= S_KEY;
}

// Obfuscated strings (XORed with 0x7A)
// "\\\\.\\pipe\\LivyLogsPipe" -> [0x26, 0x26, 0x54, 0x26, 0x54, 0x0A, 0x13, 0x0A, 0x1F, 0x26, 0x36, 0x13, 0x0C, 0x03, 0x36, 0x15, 0x1D, 0x03, 0x2A, 0x13, 0x0A, 0x1F, 0x00]
unsigned char p_name[] = {0x26, 0x26, 0x54, 0x26, 0x54, 0x0A, 0x13, 0x0A, 0x1F, 0x26, 0x36, 0x13, 0x0C, 0x03, 0x36, 0x15, 0x1D, 0x03, 0x2A, 0x13, 0x0A, 0x1F, 0x00};
// "points of damage" -> [0x0A, 0x15, 0x13, 0x14, 0x0E, 0x09, 0x5A, 0x15, 0x1C, 0x5A, 0x1E, 0x1B, 0x17, 0x1B, 0x1D, 0x1F, 0x00]
unsigned char s_dmg[] = {0x0A, 0x15, 0x13, 0x14, 0x0E, 0x09, 0x5A, 0x15, 0x1C, 0x5A, 0x1E, 0x1B, 0x17, 0x1B, 0x1D, 0x1F, 0x00};
// "looted" -> [0x16, 0x15, 0x15, 0x0E, 0x1F, 0x1E, 0x00]
unsigned char s_loot[] = {0x16, 0x15, 0x15, 0x0E, 0x1F, 0x1E, 0x00};
// "for " -> [0x1C, 0x15, 0x08, 0x5A, 0x00]
unsigned char s_for[] = {0x1C, 0x15, 0x08, 0x5A, 0x00};
// "dealt" -> [0x1E, 0x1F, 0x1B, 0x16, 0x0E, 0x00]
unsigned char s_dealt[] = {0x1E, 0x1F, 0x1B, 0x16, 0x0E, 0x00};
// "You" -> [0x23, 0x15, 0x0F, 0x00]
unsigned char s_you[] = {0x23, 0x15, 0x0F, 0x00};
// "loot" -> [0x16, 0x15, 0x15, 0x0E, 0x00]
unsigned char s_loot_type[] = {0x16, 0x15, 0x15, 0x0E, 0x00};
// "Group" -> [0x3D, 0x08, 0x15, 0x0F, 0x0A, 0x00]
unsigned char s_group[] = {0x3D, 0x08, 0x15, 0x0F, 0x0A, 0x00};

void send_event(HANDLE h, const char* t, const char* s, int d_val, const char* i) {
    char j[BUFFER_SIZE];
    sprintf(j, "{\"type\": \"%s\", \"source\": \"%s\", \"damage\": %d, \"item\": \"%s\"}\n", 
            t, s, d_val, i ? i : "");
    DWORD w;
    WriteFile(h, j, (DWORD)strlen(j), &w, NULL);
}

void p_l(HANDLE h, char* l) {
    char d_dmg[32], d_loot[32], d_for[32], d_dealt[32], d_you[32], d_lt[32], d_gr[32];
    strcpy(d_dmg, (char*)s_dmg); d(d_dmg);
    strcpy(d_loot, (char*)s_loot); d(d_loot);
    strcpy(d_for, (char*)s_for); d(d_for);
    strcpy(d_dealt, (char*)s_dealt); d(d_dealt);
    strcpy(d_you, (char*)s_you); d(d_you);
    strcpy(d_lt, (char*)s_loot_type); d(d_lt);
    strcpy(d_gr, (char*)s_group); d(d_gr);

    if (strstr(l, d_dmg)) {
        int v = 0;
        char* p = strstr(l, d_for);
        if (p) sscanf(p + 4, "%d", &v);
        send_event(h, d_dealt, d_you, v, "");
    } 
    else if (strstr(l, d_loot)) {
        char* it = strchr(l, '\'');
        if (it) {
            send_event(h, d_lt, d_gr, 0, it + 1);
        }
    }
}

int main(int a, char** v) {
    if (a < 2) return 1;

    char d_pn[64];
    strcpy(d_pn, (char*)p_name); d(d_pn);

    HANDLE hp = CreateNamedPipe(d_pn, PIPE_ACCESS_OUTBOUND, PIPE_TYPE_BYTE | PIPE_WAIT, 1, 0, 0, 0, NULL);
    if (hp == INVALID_HANDLE_VALUE) return 1;

    ConnectNamedPipe(hp, NULL);

    HANDLE hf = CreateFile(v[1], GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hf == INVALID_HANDLE_VALUE) { CloseHandle(hp); return 1; }

    SetFilePointer(hf, 0, NULL, FILE_END);

    char b[BUFFER_SIZE];
    DWORD r;

    while (1) {
        if (ReadFile(hf, b, BUFFER_SIZE - 1, &r, NULL) && r > 0) {
            b[r] = '\0';
            char* t = strtok(b, "\r\n");
            while (t != NULL) {
                p_l(hp, t);
                t = strtok(NULL, "\r\n");
            }
        } else {
            Sleep(100);
        }
    }

    CloseHandle(hf);
    CloseHandle(hp);
    return 0;
}
