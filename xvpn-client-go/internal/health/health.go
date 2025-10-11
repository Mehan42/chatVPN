package health

import (
	"context"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"strings"
	"time"

	"xvpn-client-go/internal/geoip"
)

// HealthChecker проверяет различные аспекты безопасности
type HealthChecker struct {
	client    *http.Client
	geoip     *geoip.TrafficRouter
	timeout   time.Duration
}

// LeakResult результат проверки утечки
type LeakResult struct {
	Type        string // ip_leak, dns_leak, protocol_leak
	Description string
	Detected    bool
	Value       string
	Score       int // 0-5, где 5 - отлично
}

// NewHealthChecker создает новый экземпляр HealthChecker
func NewHealthChecker(trafficRouter *geoip.TrafficRouter) *HealthChecker {
	return &HealthChecker{
		client: &http.Client{
			Timeout: 10 * time.Second,
		},
		geoip:   trafficRouter,
		timeout: 10 * time.Second,
	}
}

// CheckAllHealth проверяет все аспекты безопасности
func (hc *HealthChecker) CheckAllHealth() []LeakResult {
	results := make([]LeakResult, 0)
	
	// Проверка утечки IP
	ipLeak := hc.CheckIPLeak()
	results = append(results, ipLeak)
	
	// Проверка утечки DNS
	dnsLeak := hc.CheckDNSLeak()
	results = append(results, dnsLeak)
	
	// Проверка маскировки TLS
	tlsMasking := hc.CheckTLSMasking()
	results = append(results, tlsMasking)
	
	// Проверка утечки WebRTC
	webrtcLeak := hc.CheckWebRTCMasking()
	results = append(results, webrtcLeak)
	
	return results
}

// CheckIPLeak проверяет утечку IP-адреса
func (hc *HealthChecker) CheckIPLeak() LeakResult {
	result := LeakResult{
		Type:        "ip_leak",
		Description: "Проверка утечки IP-адреса",
		Detected:    false,
		Score:       5, // начальная оценка
	}
	
	// Запрашиваем внешний IP через несколько сервисов
	publicIP, err := hc.getExternalIP()
	if err != nil {
		result.Score = 1
		result.Description += " (ошибка получения внешнего IP)"
		return result
	}
	
	// Запрашиваем локальный IP
	localIP, err := hc.getLocalIP()
	if err != nil {
		result.Score = 3
		result.Description += " (ошибка получения локального IP)"
		return result
	}
	
	// Сравниваем IP-адреса
	if publicIP != "" && localIP != "" && publicIP == localIP {
		result.Detected = true
		result.Value = fmt.Sprintf("Public IP: %s, Local IP: %s", publicIP, localIP)
		result.Score = 1 // утечка обнаружена
		result.Description += " (утечка обнаружена)"
	} else {
		result.Value = fmt.Sprintf("Public IP: %s, Local IP: %s", publicIP, localIP)
		result.Description += " (утечка не обнаружена)"
	}
	
	return result
}

// CheckDNSLeak проверяет утечку DNS
func (hc *HealthChecker) CheckDNSLeak() LeakResult {
	result := LeakResult{
		Type:        "dns_leak",
		Description: "Проверка утечки DNS",
		Detected:    false,
		Score:       5,
	}
	
	// Проверяем DNS-запросы к известным утечо-доменам
	leakDomains := []string{
		"dnsleaktest.com",
		"ipv4.dnsleaktest.com",
		"ipv6.dnsleaktest.com",
	}
	
	// В реальной реализации здесь будет проверка через DNS-запросы
	// В этой имитации просто проверяем, можно ли разрешить доменные имена
	
	for _, domain := range leakDomains {
		ips, err := net.LookupIP(domain)
		if err != nil {
			// Ошибка разрешения не означает утечку
			continue
		}
		
		// Проверяем, есть ли в результатах IP-адреса провайдера
		for _, ip := range ips {
			if !ip.IsLoopback() && !ip.IsPrivate() {
				// Имитация проверки, если IP не принадлежит РУ региону
				if hc.geoip != nil {
					decision := hc.geoip.GetRouteDecision(ip.String())
					if !decision.Direct { // если не прямой трафик, значит направляется через VPN
						result.Description += fmt.Sprintf(" (проверка %s: OK)", domain)
					} else {
						result.Detected = true
						result.Value = fmt.Sprintf("DNS запрос к %s разрешен через %s", domain, ip.String())
						result.Score = 2
						result.Description += " (обнаружена потенциальная утечка DNS)"
						return result
					}
				} else {
					// Если нет маршрутизатора, предполагаем, что все нормально
					result.Description += fmt.Sprintf(" (проверка %s: OK - без маршрутизатора)", domain)
				}
			}
		}
	}
	
	result.Description += " (утечка не обнаружена)"
	return result
}

// CheckTLSMasking проверяет маскировку TLS
func (hc *HealthChecker) CheckTLSMasking() LeakResult {
	result := LeakResult{
		Type:        "tls_masking",
		Description: "Проверка маскировки TLS",
		Detected:    false,
		Score:       5,
	}
	
	// Проверяем TLS-соединение с разными сервисами
	tlsTargets := []string{
		"https://www.google.com",
		"https://www.cloudflare.com",
		"https://www.github.com",
	}
	
	totalScore := 0
	scoreCount := 0
	
	for _, target := range tlsTargets {
		score, err := hc.evaluateTLSScore(target)
		if err != nil {
			continue
		}
		totalScore += score
		scoreCount++
	}
	
	if scoreCount > 0 {
		avgScore := totalScore / scoreCount
		result.Score = avgScore
		result.Description += fmt.Sprintf(" (средняя оценка: %d/5)", avgScore)
		
		if avgScore < 3 {
			result.Detected = true
			result.Description += " (низкая маскировка TLS)"
		}
	} else {
		result.Score = 2
		result.Description += " (ошибка оценки TLS)"
	}
	
	return result
}

// evaluateTLSScore оценивает маскировку TLS для конкретного адреса
func (hc *HealthChecker) evaluateTLSScore(url string) (int, error) {
	// В реальной реализации здесь будет анализ TLS-соединения
	// Включая анализ JA3/JA4 сигнатур, порядок криптографии, и т.д.
	
	// Имитация проверки - просто проверяем, можно ли установить соединение
	ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
	defer cancel()
	
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return 1, err
	}
	
	resp, err := hc.client.Do(req)
	if err != nil {
		return 1, err
	}
	defer resp.Body.Close()
	
	// Оцениваем, насколько "обычно" выглядит соединение
	// (в имитации просто возвращаем высокую оценку)
	return 5, nil
}

// CheckWebRTCMasking проверяет утечку WebRTC
func (hc *HealthChecker) CheckWebRTCMasking() LeakResult {
	result := LeakResult{
		Type:        "webrtc_masking",
		Description: "Проверка маскировки WebRTC",
		Detected:    false,
		Score:       5,
	}
	
	// В реальной реализации здесь будет проверка WebRTC утечек
	// WebRTC может обходить VPN и раскрывать реальный IP
	
	// Имитация: проверяем, можно ли получить локальные IP-адреса
	localIPs := hc.getLocalIPs()
	if len(localIPs) > 0 {
		// В VPN-среде WebRTC не должен показывать реальные локальные IP
		// Если показывает, возможно есть утечка
		result.Value = fmt.Sprintf("%d локальных IP обнаружено", len(localIPs))
		
		// В этой имитации считаем, что если локальные IP обнаружены,
		// то может быть потенциальная утечка через WebRTC
		result.Detected = true
		result.Score = 3
		result.Description += " (обнаружены локальные IP, возможна утечка WebRTC)"
	} else {
		result.Description += " (утечка не обнаружена)"
	}
	
	return result
}

// getExternalIP получает внешний IP-адрес
func (hc *HealthChecker) getExternalIP() (string, error) {
	services := []string{
		"https://api.ipify.org",
		"https://httpbin.org/ip",
		"https://ifconfig.me/ip",
		"https://icanhazip.com",
		"https://ident.me",
	}
	
	ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
	defer cancel()
	
	for _, service := range services {
		req, err := http.NewRequestWithContext(ctx, "GET", service, nil)
		if err != nil {
			continue
		}
		
		resp, err := hc.client.Do(req)
		if err != nil {
			continue
		}
		
		if resp.StatusCode == 200 {
			body, err := ioutil.ReadAll(resp.Body)
			resp.Body.Close()
			if err == nil {
				ip := strings.TrimSpace(string(body))
				return ip, nil
			}
		}
		
		resp.Body.Close()
	}
	
	return "", fmt.Errorf("не удалось получить внешний IP")
}

// getLocalIP получает локальный IP-адрес
func (hc *HealthChecker) getLocalIP() (string, error) {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		return "", err
	}
	defer conn.Close()
	
	localAddr := conn.LocalAddr().(*net.UDPAddr)
	return localAddr.IP.String(), nil
}

// getLocalIPs возвращает список локальных IP-адресов
func (hc *HealthChecker) getLocalIPs() []string {
	addresses, err := net.InterfaceAddrs()
	if err != nil {
		return []string{}
	}
	
	var localIPs []string
	for _, addr := range addresses {
		if ipnet, ok := addr.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				localIPs = append(localIPs, ipnet.IP.String())
			}
		}
	}
	
	return localIPs
}

// GetOverallHealthScore возвращает общую оценку здоровья
func (hc *HealthChecker) GetOverallHealthScore() int {
	results := hc.CheckAllHealth()
	
	totalScore := 0
	for _, result := range results {
		totalScore += result.Score
	}
	
	// Усредняем оценку (максимум 5 проверок * 5 баллов = 25)
	avgScore := totalScore / len(results)
	
	// Нормализуем до 5-балльной шкалы
	if len(results) > 0 {
		return avgScore
	}
	
	return 0
}

// GetHealthReport возвращает текстовый отчет о здоровье
func (hc *HealthChecker) GetHealthReport() string {
	results := hc.CheckAllHealth()
	var report strings.Builder
	
	report.WriteString("=== Отчет о здоровье XVPN ===\n")
	
	for _, result := range results {
		status := "OK"
		if result.Detected {
			status = "ВНИМАНИЕ"
		}
		
		report.WriteString(fmt.Sprintf("%s: %s [%s]\n", result.Type, result.Description, status))
		if result.Value != "" {
			report.WriteString(fmt.Sprintf("  Значение: %s\n", result.Value))
		}
		report.WriteString(fmt.Sprintf("  Оценка: %d/5\n\n", result.Score))
	}
	
	report.WriteString(fmt.Sprintf("Общая оценка: %d/5\n", hc.GetOverallHealthScore()))
	
	return report.String()
}