# Dingtian Binary Relay – Direct TCP/UDP Integration

## English

**Overview**
Dingtian Binary Relay is a Home Assistant integration providing direct TCP/UDP communication with Dingtian DT-Rxxx relay boards using the Dingtian Binary Protocol. It does **not require MQTT or a broker (Mosquitto)** — communication is peer-to-device which reduces latency and system complexity.

**Key features**
- Direct binary TCP/UDP communication (no MQTT broker required)
- Autodiscovery via UDP multicast
- Multi-board support (multiple config entries)
- Dynamic channel detection (2/4/8/16/32)
- Lockout and pulse (momentary) options per device
- Binary sensors for inputs and switches for outputs

**Supported devices**
DT-R002, DT-R004, DT-R008, DT-R016, DT-R032
(Other variants compatible if they implement Dingtian Binary Protocol.)

**Quick start**
1. Install integration via HACS (add repo: https://github.com/adres433/ha-dtrelay-binary)
2. Add integration in Home Assistant settings → Devices & Services → Add integration
3. Use Discover to find boards on LAN or configure manually (IP, ports, protocol)

**Binary vs MQTT (comparison)**
| Feature | Binary Integration | MQTT Integration |
|---|---:|---:|
| Latency | ✅ Lowest (direct) | ⚠️ Depends on broker |
| Configuration | ✅ Simple (GUI) | ⚠️ Requires broker setup |
| Resource usage | ✅ Low | ⚠️ Higher (broker) |
| Complexity | ✅ Minimal | ⚠️ Additional components |

---

## Polski

**Opis**
Dingtian Binary Relay to integracja Home Assistant zapewniająca bezpośrednią komunikację TCP/UDP z płytkami przekaźnikowymi Dingtian DT-Rxxx używając protokołu Dingtian Binary. Integracja **nie wymaga MQTT ani brokera (Mosquitto)** — komunikacja jest bezpośrednia, co zmniejsza opóźnienia i złożoność systemu.

**Najważniejsze cechy**
- Bezpośrednia komunikacja binarna TCP/UDP (bez brokera MQTT)
- Autodetekcja urządzeń przez UDP multicast
- Obsługa wielu płytek (wiele wpisów konfiguracyjnych)
- Dynamiczne wykrywanie liczby kanałów (2/4/8/16/32)
- Opcje lockout i pulse (chwilowe) per urządzenie
- Binary sensor i switch dla wejść/wyjść

**Obsługiwane urządzenia**
DT-R002, DT-R004, DT-R008, DT-R016, DT-R032
(Inne warianty kompatybilne, jeżeli stosują Dingtian Binary Protocol.)

**Szybki start**
1. Zainstaluj integrację przez HACS (repo: https://github.com/adres433/ha-dtrelay-binary)
2. Dodaj integrację w Home Assistant: Ustawienia → Urządzenia i usługi → Dodaj integrację
3. Użyj opcji Discover by wykryć urządzenia lub skonfiguruj ręcznie (IP, porty, protokół)

**Binary vs MQTT (porównanie)**
| Funkcja | Integracja binarna | Integracja MQTT |
|---|---:|---:|
| Opóźnienie | ✅ Najniższe (bezpośrednie) | ⚠️ Zależne od brokera |
| Konfiguracja | ✅ Prosta (GUI) | ⚠️ Wymaga brokera |
| Zużycie zasobów | ✅ Niskie | ⚠️ Wyższe (broker) |
| Złożoność | ✅ Minimalna | ⚠️ Dodatkowe komponenty |
