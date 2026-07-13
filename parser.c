/*
 * LivyLogs - Combat Log Analyzer
 * Copyright (c) 2026 Livy
 * Licensed under the GNU General Public License v3.0.
 */

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
unsigned char s_no_longer_intimidated[] = {0x14, 0x15, 0x5a, 0x16, 0x15, 0x14, 0x1d, 0x1f, 0x08, 0x5a, 0x13, 0x14, 0x0e, 0x13, 0x17, 0x13, 0x1e, 0x1b, 0x0e, 0x1f, 0x1e, 0x00};
unsigned char s_poison[] = {0x1a, 0x15, 0x13, 0x9, 0x15, 0x14, 0x00};
unsigned char s_resists[] = {0x8, 0x1f, 0x9, 0x13, 0x9, 0xe, 0x9, 0x00};
unsigned char s_incapacitated[] = {0x13, 0x14, 0x19, 0x1b, 0x1a, 0x1b, 0x19, 0x13, 0xe, 0x1b, 0xe, 0x1f, 0x1e, 0x00};
unsigned char s_you_have_been[] = {0x3, 0x15, 0xf, 0x5a, 0x12, 0x1b, 0x2c, 0x1f, 0x5a, 0x18, 0x1f, 0x1f, 0x14, 0x00};
unsigned char s_has_been[] = {0x12, 0x1b, 0x9, 0x5a, 0x18, 0x1f, 0x1f, 0x14, 0x00};
unsigned char s_kill[] = {0x11, 0x13, 0x16, 0x16, 0x00};

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
    int mob_count;
    double total_xp;
    time_t last_hit;
} PlayerStats;

PlayerStats g_players[MAX_PLAYERS];
int g_player_count = 0;

HWND target_hwnd = NULL;
DWORD python_pid = 0;
HANDLE g_pipe = INVALID_HANDLE_VALUE;

void send_raw_event(HANDLE h, const char* msg) {
    if (h == INVALID_HANDLE_VALUE) return;
    DWORD b_w;
    if (!WriteFile(h, msg, strlen(msg), &b_w, NULL)) {
        // Pipe might be broken
    }
    WriteFile(h, "\n", 1, &b_w, NULL);
}

// Internal helpers
PlayerStats* get_player(const char* name) {
    if (!name || !*name) return NULL;
    char n[128];
    strncpy(n, name, 127); n[127] = '\0';
    if (_stricmp(n, "Damage You") == 0) strcpy(n, "You");
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
        g_players[g_player_count].mob_count = 0;
        g_players[g_player_count].total_xp = 0;
        g_players[g_player_count].last_hit = 0;
        return &g_players[g_player_count++];
    }
    return NULL;
}

void a_o_t(BOOL s_s) {
    // Moved to Python
}

void u_v() {
    // Moved to Python
}

void c_o() {
    // Process cleanup is now primarily handled by the Python UI
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
    
    const char* real_s = s_c;
    if (_stricmp(real_s, "Damage You") == 0) real_s = "You";
    const char* real_t = t_g;
    if (_stricmp(real_t, "Damage You") == 0) real_t = "You";

    e_j(real_s, e_s);
    e_j(real_t, e_t);
    e_j(a, e_a);
    e_j(i_t, e_i);

    sprintf(j, "{\"type\": \"%s\", \"source\": \"%s\", \"target\": \"%s\", \"damage\": %.2f, \"healing\": %.2f, \"ability\": \"%s\", \"item\": \"%s\", \"is_mitigated\": %s}\n",
            t, e_s, e_t, d_m, h_l, e_a, e_i, m_t ? "true" : "false");
    
    DWORD w_b;
    if (!WriteFile(h, j, (DWORD)strlen(j), &w_b, NULL)) {
        // Handle error
    }
}

void s_s(HANDLE h) {
    for(int i=0; i<g_player_count; i++) {
        char j[BUFFER_SIZE];
        char e_n[256];
        char* n = g_players[i].name;
        if (_stricmp(n, "Damage You") == 0) n = "You";
        e_j(n, e_n);
        sprintf(j, "{\"type\": \"stats\", \"name\": \"%s\", \"damage\": %.2f, \"healing\": %.2f, \"taken\": %.2f, \"hits\": %d, \"misses\": %d, \"avoided\": %d, \"aoe\": %d, \"loot\": %d, \"mobs\": %d, \"xp\": %.2f}\n",
                e_n, g_players[i].damage, g_players[i].healing, g_players[i].taken, g_players[i].hits, g_players[i].misses, g_players[i].avoided, g_players[i].aoe_hits, g_players[i].loot_count, g_players[i].mob_count, g_players[i].total_xp);
        DWORD w_b;
        if (!WriteFile(h, j, (DWORD)strlen(j), &w_b, NULL)) {
            // Handle error
        }
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
    // Guard against excessively long lines (over 4096 chars)
    if (strlen(l) > 4096) return;

    char* clean = l;
    if (l[0] == '[') {
        char* end_bracket = strchr(l, ']');
        if (end_bracket) clean = end_bracket + 1;
        // Check for double bracket format [Spatial] [00:00:00] [GROUP]
        if (clean[0] == ' ' && clean[1] == '[') {
            char* second_bracket = strchr(clean + 1, ']');
            if (second_bracket) clean = second_bracket + 1;
            if (clean[0] == ' ' && clean[1] == '[') {
                char* third_bracket = strchr(clean + 1, ']');
                if (third_bracket) clean = third_bracket + 1;
            }
        }
    }
    while(*clean == ' ') clean++;
    // SWG logs often have a timestamp like 03:20:00 without brackets
    if (isdigit(clean[0]) && isdigit(clean[1]) && clean[2] == ':') {
        clean += 9;
    }
    while(*clean == ' ') clean++;
    // Check for [GROUP] after timestamp if not caught by bracket logic
    if (clean[0] == '[') {
        char* group_bracket = strchr(clean, ']');
        if (group_bracket) clean = group_bracket + 1;
    }
    while(*clean == ' ') clean++;

    char lower[BUFFER_SIZE];
    for(int i=0; clean[i]; i++) lower[i] = tolower(clean[i]);
    lower[strlen(clean)] = '\0';

    char s_ap[32], s_lt[32], s_fr[32], s_hd[32], s_ar[32], s_l_key[32], s_ac[32], s_he[32], s_de[32], s_tk[32], s_od[32], s_di[32], s_f[32], s_o[32], s_t[32], s_y[32], s_nli[64], s_poi[32], s_res[32], s_inc[32], s_yhb[32], s_hb[32];

    // Incapacitated tracking
    strcpy(s_inc, (char*)s_incapacitated); d(s_inc);
    if (strstr(lower, s_inc)) {
        char target[128] = "Unknown";
        int found = 0;
        
        strcpy(s_yhb, (char*)s_you_have_been); d(s_yhb);
        if (strstr(lower, s_yhb)) {
            strcpy(target, "You");
            found = 1;
        } else {
            strcpy(s_hb, (char*)s_has_been); d(s_hb);
            char* p_hb = s_i_s(clean, s_hb);
            if (p_hb) {
                int t_len = p_hb - clean;
                if (t_len > 127) t_len = 127;
                if (t_len > 0) {
                    strncpy(target, clean, t_len); target[t_len] = '\0';
                    while(strlen(target) > 0 && target[strlen(target)-1] == ' ') target[strlen(target)-1] = '\0';
                    found = 1;
                }
            }
        }
        
        if (found) {
            char j[BUFFER_SIZE];
            char e_n[256];
            e_j(target, e_n);
            sprintf(j, "{\"type\": \"incapacitated\", \"target\": \"%s\"}\n", e_n);
            send_raw_event(h, j);
            // Don't return, might also be a death or other event in some logs
        }
    }

    // Poison tracking: "Target resists your poison" or "You apply poison to Target"
    strcpy(s_res, (char*)s_resists); d(s_res);
    if (strstr(lower, s_res) && strstr(lower, "poison")) {
        char* p_res = s_i_s(clean, s_res);
        if (p_res) {
            char target[128] = "Unknown";
            int t_len = p_res - clean;
            if (t_len > 127) t_len = 127;
            if (t_len > 0) {
                strncpy(target, clean, t_len); target[t_len] = '\0';
                while(strlen(target) > 0 && target[strlen(target)-1] == ' ') target[strlen(target)-1] = '\0';
                
                char j[BUFFER_SIZE];
                char e_n[256];
                e_j(target, e_n);
                sprintf(j, "{\"type\": \"poison_resist\", \"target\": \"%s\"}\n", e_n);
                send_raw_event(h, j);
                return;
            }
        }
    }

    strcpy(s_poi, (char*)s_poison); d(s_poi);
    if (strstr(lower, s_poi) && strstr(lower, "you apply")) {
        // "You apply poison to Target"
        char* p_to = strstr(lower, " to ");
        if (p_to) {
            char target[128] = "Unknown";
            char* p_target = clean + (p_to - lower) + 4;
            strncpy(target, p_target, 127); target[127] = '\0';
            // Remove trailing period if present
            if (strlen(target) > 0 && target[strlen(target)-1] == '.') target[strlen(target)-1] = '\0';
            while(strlen(target) > 0 && (target[strlen(target)-1] == ' ' || target[strlen(target)-1] == '!')) target[strlen(target)-1] = '\0';

            char j[BUFFER_SIZE];
            char e_n[256];
            e_j(target, e_n);
            sprintf(j, "{\"type\": \"poison\", \"source\": \"You\", \"target\": \"%s\"}\n", e_n);
            send_raw_event(h, j);
            return;
        }
    }

    // No longer intimidated
    strcpy(s_nli, (char*)s_no_longer_intimidated); d(s_nli);
    if (strstr(lower, s_nli)) {
        char* p = s_i_s(clean, s_nli);
        if (p) {
            char name[128] = "Unknown";
            int n_len = p - clean;
            if (n_len > 127) n_len = 127;
            if (n_len > 0) {
                strncpy(name, clean, n_len); name[n_len] = '\0';
                while(strlen(name) > 0 && name[strlen(name)-1] == ' ') name[strlen(name)-1] = '\0';
                
                char j[BUFFER_SIZE];
                char e_n[256];
                e_j(name, e_n);
                sprintf(j, "{\"type\": \"status_removed\", \"target\": \"%s\", \"status\": \"intimidate\"}\n", e_n);
                send_raw_event(h, j);
                return;
            } else if (n_len == 0) {
                 // "No longer intimidated..." starting the line might mean "You" in some games
                 // but let's assume it's "[Name] no longer intimidated"
            }
        }
    }

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
            while(strlen(name) > 0 && name[strlen(name)-1] == ' ') name[strlen(name)-1] = '\0';

            strcpy(s_fr, (char*)s_from); d(s_fr);
            char* p_from = s_i_s(p_loot, s_fr);
            if (p_from) {
                int i_start = 7; // Length of "looted "
                int i_len = p_from - (p_loot + i_start);
                if (i_len > 255) i_len = 255;
                if (i_len > 0) {
                    strncpy(item, p_loot + i_start, i_len); item[i_len] = '\0';
                    while(strlen(item) > 0 && item[strlen(item)-1] == ' ') item[strlen(item)-1] = '\0';
                    
                    char target[256] = "Unknown";
                    char* p_after_from = p_from + 5; // Length of "from "
                    if (p_after_from < clean + strlen(clean)) {
                        strncpy(target, p_after_from, 255);
                        target[255] = '\0';
                        // Remove trailing period if present
                        if (strlen(target) > 0 && target[strlen(target)-1] == '.') target[strlen(target)-1] = '\0';
                        while(strlen(target) > 0 && (target[strlen(target)-1] == ' ' || target[strlen(target)-1] == '!')) target[strlen(target)-1] = '\0';
                    }

                    double credits = 0;
                    char* p_cred = strstr(item, " credits");
                    if (p_cred) {
                        sscanf(item, "%lf", &credits);
                        // Filter erroneous data (over 1 billion as requested)
                        if (credits >= 1000000000.0) return;
                    }

                    char j[BUFFER_SIZE];
                    sprintf(j, "{\"type\": \"loot\", \"source\": \"%s\", \"item\": \"%s\", \"credits\": %.2f, \"target\": \"%s\"}\n", name, item, credits, target);
                    send_raw_event(h, j);
                    
                    // Also send as a stat update to ensure it shows up in basic counters
                    PlayerStats* ps = get_player(name);
                    if(ps) {
                        ps->loot_count++;
                        char sj[BUFFER_SIZE];
                        char e_n[256];
                        e_j(ps->name, e_n);
                        sprintf(sj, "{\"type\": \"stats\", \"name\": \"%s\", \"damage\": %.2f, \"healing\": %.2f, \"taken\": %.2f, \"hits\": %d, \"misses\": %d, \"avoided\": %d, \"aoe\": %d, \"loot\": %d, \"mobs\": %d, \"xp\": %.2f}\n",
                                e_n, ps->damage, ps->healing, ps->taken, ps->hits, ps->misses, ps->avoided, ps->aoe_hits, ps->loot_count, ps->mob_count, ps->total_xp);
                        send_raw_event(h, sj);
                    }
                    return;
                }
            }
        }
    }

    // XP Parsing: "You receive <value> points of <name> experience"
    if (strstr(lower, "you receive ") && strstr(lower, " experience")) {
        char* p_xp = strstr(lower, "you receive ");
        if (p_xp) {
            double amount = 0;
            if (sscanf(clean + (p_xp - lower) + 12, "%lf", &amount) == 1) {
                // Filter erroneous data (over 1 billion as requested)
                if (amount >= 1000000000.0) return;

                PlayerStats* ps = get_player("You");
                if (ps) {
                    ps->total_xp += amount;
                    // Removed redundant s_s(h) here
                }
                
                // Find experience type name
                char xp_type[64] = "Unknown";
                char* p_of = strstr(lower, " points of ");
                if (p_of) {
                    int type_start = (p_of - lower) + 11;
                    char* p_exp = strstr(lower + type_start, " experience");
                    if (p_exp) {
                        int type_len = p_exp - (lower + type_start);
                        if (type_len > 63) type_len = 63;
                        if (type_len > 0) {
                            strncpy(xp_type, clean + type_start, type_len);
                            xp_type[type_len] = '\0';
                        }
                    }
                }

                char j[BUFFER_SIZE];
                sprintf(j, "{\"type\": \"xp\", \"source\": \"You\", \"amount\": %.2f, \"xp_type\": \"%s\"}\n", amount, xp_type);
                send_raw_event(h, j);
            }
        }
    }

    // Chat parsing for [Groupchat]
    if (l[0] == '[') {
        char* first_bracket_end = strchr(l, ']');
        if (first_bracket_end) {
            char channel[64];
            int c_len = first_bracket_end - (l + 1);
            if (c_len > 63) c_len = 63;
            strncpy(channel, l + 1, c_len);
            channel[c_len] = '\0';

            if (_stricmp(channel, "Groupchat") == 0) {
                char* after_channel = first_bracket_end + 1;
                while (*after_channel == ' ') after_channel++;
                
                // Format is usually "[Groupchat] PlayerName: message"
                char* colon = strchr(after_channel, ':');
                if (colon) {
                    char name[128];
                    int n_len = colon - after_channel;
                    if (n_len > 127) n_len = 127;
                    strncpy(name, after_channel, n_len);
                    name[n_len] = '\0';
                    
                    char* msg = colon + 1;
                    while (*msg == ' ') msg++;
                    
                    char j[BUFFER_SIZE];
                    char e_n[256], e_m[BUFFER_SIZE];
                    e_j(name, e_n);
                    e_j(msg, e_m);
                    sprintf(j, "{\"type\": \"chat\", \"channel\": \"Groupchat\", \"source\": \"%s\", \"message\": \"%s\"}\n", e_n, e_m);
                    send_raw_event(h, j);
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
            while(strlen(name) > 0 && name[strlen(name)-1] == ' ') name[strlen(name)-1] = '\0';
            
            strcpy(s_ac, (char*)s_activity); d(s_ac);
            strcpy(s_di, (char*)s_died); d(s_di);
            s_e(h, s_ac, name, "Unknown", 0, 0, "", s_di, 0);

            // If an NPC died, find who hit them last and give them the credit
            // OR if it's "You have defeated...", source is "You"
            // For now, let's look for "You have defeated " pattern too.
            if (_stricmp(name, "You") == 0) {
                // This usually means the line was "You have defeated [Target]."
                // But in SWG it's often "[Target] has been defeated."
            }

            // Simple heuristic for "Mobs" - if a player dies, they aren't a mob usually
            // but for this app, we just count deaths that aren't "You" or known players?
            // Actually, the request says "npcs that player killed".
            // If the line is "You have defeated [NPC]!", then source=You, target=NPC.
            return;
        }
    }

    // You have defeated ...
    if (strstr(lower, "you have defeated ")) {
        char* p_def = strstr(lower, "you have defeated ");
        if (p_def) {
            PlayerStats* ps = get_player("You");
            if (ps) {
                ps->mob_count++;
                char s_ki[64]; strcpy(s_ki, (char*)s_kill); d(s_ki);
                s_e(h, s_ki, "You", "", 0, 0, "", "", 0);
            }
        }
    }
    
    // [Player] has defeated [NPC]!
    char* p_has_def = strstr(lower, " has defeated ");
    if (p_has_def) {
        int n_len = p_has_def - lower;
        char name[128];
        if (n_len > 127) n_len = 127;
        strncpy(name, clean, n_len); name[n_len] = '\0';
        while(strlen(name) > 0 && name[strlen(name)-1] == ' ') name[strlen(name)-1] = '\0';
        
        PlayerStats* ps = get_player(name);
        if (ps) {
            ps->mob_count++;
            // Notify Python about the kill
            char s_ki[64]; strcpy(s_ki, (char*)s_kill); d(s_ki);
            s_e(h, s_ki, name, "", 0, 0, "", "", 0);
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
                // Filter erroneous data (over 1 billion as requested)
                if (amount >= 1000000000.0) return;

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
                    int t_len = p_for - (p_on + 4); 
                    if (t_len > 0) {
                        if (t_len > 127) t_len = 127;
                        strncpy(target, p_on + 4, t_len); target[t_len] = '\0';
                    }
                } else {
                    int t_len = p_for - (p_act + strlen(actions[i]));
                    if (t_len > 0) {
                        if (t_len > 127) t_len = 127;
                        strncpy(target, p_act + strlen(actions[i]), t_len); target[t_len] = '\0';
                    }
                }

                // Cleanup target: remove " points of damage" if it's there (shouldn't be with " for " logic but safe)
                char* p_points = strstr(target, " points");
                if (p_points) *p_points = '\0';

                // Cleanup names: remove leading "Damage " if it was accidentally captured
                if (_strnicmp(source, "Damage ", 7) == 0) memmove(source, source + 7, strlen(source) - 6);
                if (_strnicmp(target, "Damage ", 7) == 0) memmove(target, target + 7, strlen(target) - 6);

                // Second pass to ensure "Damage You" becomes "You"
                if (_stricmp(source, "Damage You") == 0) strcpy(source, "You");
                if (_stricmp(target, "Damage You") == 0) strcpy(target, "You");

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
    char* d_pn = "\\\\.\\pipe\\LivyLogsPipe";
    
    char pid_file[256];
    sprintf(pid_file, "engine_pid_%lu.tmp", GetCurrentProcessId());
    
    // Create signal file IMMEDIATELY to show we are alive
    char pid_file_path[MAX_PATH];
    GetModuleFileName(NULL, pid_file_path, MAX_PATH);
    char* last_slash = strrchr(pid_file_path, '\\');
    if (last_slash) *last_slash = '\0';
    char full_tmp_path[MAX_PATH];
    sprintf(full_tmp_path, "%s\\%s", pid_file_path, pid_file);

    printf("Starting engine PID %lu\n", GetCurrentProcessId());
    
    // Create signal file IMMEDIATELY to show we are alive
    FILE* pf_init = fopen(full_tmp_path, "wb");
    if (pf_init) {
        fprintf(pf_init, "%lu", GetCurrentProcessId());
        fflush(pf_init);
        fclose(pf_init);
    }

    while (1) {
        HANDLE hp = CreateNamedPipe(d_pn, PIPE_ACCESS_OUTBOUND, PIPE_TYPE_BYTE | PIPE_WAIT, 1, 65536, 65536, 0, NULL);
        if (hp == INVALID_HANDLE_VALUE) { 
            // If pipe exists, maybe another instance is running? 
            // Since we cleared c_o(), this is possible if Python didn't kill it.
            Sleep(500); continue; 
        }
        g_pipe = hp;

        if (ConnectNamedPipe(hp, NULL) || GetLastError() == ERROR_PIPE_CONNECTED) {
            FILE* pf = fopen(full_tmp_path, "wb");
            if (pf) {
                fprintf(pf, "%lu", GetCurrentProcessId());
                fflush(pf);
                fclose(pf);
            }
            // Signal connection success for debugging
            // (Optional: write to engine_debug.txt if needed)
            
            HANDLE hf = CreateFile(l_p, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
            if (hf != INVALID_HANDLE_VALUE) {
                // If it's a test log, we might want to start from the beginning 
                // but usually for combat logs we want the end.
                if (strstr(l_p, "test_chatlog.txt") == NULL) {
                    SetFilePointer(hf, 0, NULL, FILE_END);
                }

                char b_buf[BUFFER_SIZE];
                DWORD r_b;
                char l_o[BUFFER_SIZE] = "";
                time_t last_sync = time(NULL);

                while (1) {
                    if (ReadFile(hf, b_buf, BUFFER_SIZE - 2, &r_b, NULL) && r_b > 0) {
                        b_buf[r_b] = '\0';
                        if (strlen(l_o) + r_b < BUFFER_SIZE * 2) {
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
                            if (strlen(line) < BUFFER_SIZE) strcpy(l_o, line);
                            else l_o[0] = '\0';
                        } else {
                            l_o[0] = '\0';
                        }
                        // Added a tiny sleep to prevent pipe flooding and high CPU during catch-up
                        Sleep(1);
                    } else {
                        // Check if pipe is still broken by trying a tiny write
                        DWORD w_b;
                        // Use a non-empty string to ensure WriteFile actually does something
                        // We use a specific non-printable character to minimize risk of collision
                        if (!WriteFile(hp, "\x01", 1, &w_b, NULL) && GetLastError() != ERROR_SUCCESS) {
                            break; // Pipe broken
                        }
                        Sleep(200);
                    }

                    time_t now = time(NULL);
                    if (now - last_sync >= 1) {
                        s_s(hp);
                        last_sync = now;
                    }
                }
                CloseHandle(hf);
            }
        }
        DisconnectNamedPipe(hp);
        CloseHandle(hp);
        g_pipe = INVALID_HANDLE_VALUE;
        // Remove signal file when pipe is closed so Python doesn't try to connect
        DeleteFile(full_tmp_path);
        Sleep(500);
    }
}

int APIENTRY WinMain(HINSTANCE hInst, HINSTANCE hPrevInst, LPSTR lpCmdLine, int nCmdShow) {
    int a = __argc;
    char** v = __argv;
    c_o();
    
    if (a >= 2) {
        printf("[DEBUG] Engine starting pipeline for log: %s\n", v[1]);
        fflush(stdout);
        e_t(v[1]);
    }

    while (1) {
        // If Python dies, the engine should also eventually exit
        // We can check if any pythonw.exe is running if we don't have a direct PID
        // but for now, we just stay alive or check for a specific parent process.
        // Simplified: the engine will be killed by the Python UI on start anyway.
        Sleep(1000); 
    }
    return 0;
}
