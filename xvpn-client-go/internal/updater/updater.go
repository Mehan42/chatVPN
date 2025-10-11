package updater

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"
)

// UpdateInfo информация об обновлении
type UpdateInfo struct {
	Version     string `json:"version"`
	URL         string `json:"url"`
	Checksum    string `json:"checksum"`
	Size        int64  `json:"size"`
	ReleaseDate time.Time `json:"release_date"`
	Notes       string `json:"notes"`
	Mandatory   bool   `json:"mandatory"`
}

// UpdateChecker проверяет наличие обновлений
type UpdateChecker struct {
	apiEndpoint  string
	currentVersion string
	updateChannel string
	checkInterval time.Duration
	lastCheck    time.Time
	logger        *log.Logger
}

// NewUpdateChecker создает новый экземпляр UpdateChecker
func NewUpdateChecker(apiEndpoint, currentVersion, channel string) *UpdateChecker {
	return &UpdateChecker{
		apiEndpoint:    apiEndpoint,
		currentVersion: currentVersion,
		updateChannel:  channel,
		checkInterval:  24 * time.Hour, // По умолчанию проверяем раз в день
		logger:         log.Default(),
	}
}

// CheckForUpdates проверяет наличие обновлений
func (uc *UpdateChecker) CheckForUpdates() (*UpdateInfo, error) {
	uc.logger.Printf("Проверка обновлений для версии %s", uc.currentVersion)
	
	// Формируем URL для проверки обновлений
	url := fmt.Sprintf("%s/updates/check?version=%s&channel=%s&os=%s&arch=%s", 
		uc.apiEndpoint, uc.currentVersion, uc.updateChannel, runtime.GOOS, runtime.GOARCH)
	
	// Выполняем HTTP-запрос
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	
	resp, err := client.Get(url)
	if err != nil {
		return nil, fmt.Errorf("ошибка выполнения запроса: %v", err)
	}
	defer resp.Body.Close()
	
	// Проверяем код ответа
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	// Читаем тело ответа
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("ошибка чтения ответа: %v", err)
	}
	
	// Парсим JSON
	var updateInfo UpdateInfo
	err = json.Unmarshal(body, &updateInfo)
	if err != nil {
		return nil, fmt.Errorf("ошибка парсинга JSON: %v", err)
	}
	
	// Обновляем время последней проверки
	uc.lastCheck = time.Now()
	
	// Если версия та же, что и текущая, возвращаем nil
	if updateInfo.Version == uc.currentVersion {
		uc.logger.Printf("Обновлений не найдено")
		return nil, nil
	}
	
	uc.logger.Printf("Найдено обновление до версии %s", updateInfo.Version)
	return &updateInfo, nil
}

// DownloadUpdate загружает обновление
func (uc *UpdateChecker) DownloadUpdate(updateInfo *UpdateInfo) (string, error) {
	uc.logger.Printf("Загрузка обновления версии %s", updateInfo.Version)
	
	// Создаем временный файл для загрузки
	tempDir := os.TempDir()
	filename := fmt.Sprintf("xvpn-update-%s-%s-%s", updateInfo.Version, runtime.GOOS, runtime.GOARCH)
	
	// Для Windows добавляем .exe
	if runtime.GOOS == "windows" {
		filename += ".exe"
	}
	
	tempFile := filepath.Join(tempDir, filename)
	
	// Создаем файл
	out, err := os.Create(tempFile)
	if err != nil {
		return "", fmt.Errorf("ошибка создания файла: %v", err)
	}
	defer out.Close()
	
	// Выполняем HTTP-запрос для загрузки
	client := &http.Client{
		Timeout: 5 * time.Minute, // Большой таймаут для загрузки
	}
	
	resp, err := client.Get(updateInfo.URL)
	if err != nil {
		return "", fmt.Errorf("ошибка загрузки файла: %v", err)
	}
	defer resp.Body.Close()
	
	// Проверяем код ответа
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	// Копируем данные в файл
	_, err = io.Copy(out, resp.Body)
	if err != nil {
		return "", fmt.Errorf("ошибка записи в файл: %v", err)
	}
	
	// Проверяем контрольную сумму
	if updateInfo.Checksum != "" {
		valid, err := uc.verifyChecksum(tempFile, updateInfo.Checksum)
		if err != nil {
			return "", fmt.Errorf("ошибка проверки контрольной суммы: %v", err)
		}
		
		if !valid {
			// Удаляем файл при несовпадении
			os.Remove(tempFile)
			return "", fmt.Errorf("контрольная сумма не совпадает")
		}
	}
	
	uc.logger.Printf("Обновление загружено в %s", tempFile)
	return tempFile, nil
}

// verifyChecksum проверяет контрольную сумму файла
func (uc *UpdateChecker) verifyChecksum(filePath, expectedHash string) (bool, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return false, err
	}
	defer file.Close()
	
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return false, err
	}
	
	actualHash := hex.EncodeToString(hash.Sum(nil))
	return actualHash == expectedHash, nil
}

// ApplyUpdate применяет обновление
func (uc *UpdateChecker) ApplyUpdate(updateFile string) error {
	uc.logger.Printf("Применение обновления из %s", updateFile)
	
	// Получаем путь к текущему исполняемому файлу
	execPath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("ошибка получения пути к исполняемому файлу: %v", err)
	}
	
	// Создаем резервную копию текущего файла
	backupPath := execPath + ".bak"
	err = uc.createBackup(execPath, backupPath)
	if err != nil {
		return fmt.Errorf("ошибка создания резервной копии: %v", err)
	}
	
	// Заменяем текущий файл обновлением
	err = uc.replaceExecutable(execPath, updateFile)
	if err != nil {
		// При ошибке восстанавливаем резервную копию
		uc.restoreBackup(backupPath, execPath)
		return fmt.Errorf("ошибка замены исполняемого файла: %v", err)
	}
	
	// Удаляем резервную копию
	os.Remove(backupPath)
	
	// Удаляем временный файл
	os.Remove(updateFile)
	
	uc.logger.Printf("Обновление применено успешно")
	return nil
}

// createBackup создает резервную копию файла
func (uc *UpdateChecker) createBackup(originalPath, backupPath string) error {
	input, err := ioutil.ReadFile(originalPath)
	if err != nil {
		return err
	}
	
	return ioutil.WriteFile(backupPath, input, 0644)
}

// restoreBackup восстанавливает резервную копию файла
func (uc *UpdateChecker) restoreBackup(backupPath, originalPath string) error {
	input, err := ioutil.ReadFile(backupPath)
	if err != nil {
		return err
	}
	
	return ioutil.WriteFile(originalPath, input, 0644)
}

// replaceExecutable заменяет исполняемый файл
func (uc *UpdateChecker) replaceExecutable(oldPath, newPath string) error {
	// В Unix-системах просто перемещаем файл
	if runtime.GOOS != "windows" {
		// Сначала делаем новый файл исполняемым
		err := os.Chmod(newPath, 0755)
		if err != nil {
			return err
		}
		
		// Удаляем старый файл
		err = os.Remove(oldPath)
		if err != nil {
			return err
		}
		
		// Переименовываем новый файл
		return os.Rename(newPath, oldPath)
	}
	
	// В Windows перемещение исполняемого файла, который сейчас запущен, невозможно
	// Поэтому создаем командный файл для замены после завершения
	return uc.createWindowsUpdateScript(oldPath, newPath)
}

// createWindowsUpdateScript создает скрипт для обновления в Windows
func (uc *UpdateChecker) createWindowsUpdateScript(oldPath, newPath string) error {
	scriptContent := fmt.Sprintf(`
@echo off
echo Обновление XVPN...
timeout /t 2 /nobreak >nul
del "%s"
move "%s" "%s"
echo Обновление завершено. Перезапуск...
"%s"
`, oldPath, newPath, oldPath, oldPath)
	
	scriptPath := oldPath + ".bat"
	return ioutil.WriteFile(scriptPath, []byte(scriptContent), 0755)
}

// AutoUpdate автоматически проверяет и применяет обновления
func (uc *UpdateChecker) AutoUpdate() (*UpdateInfo, error) {
	// Проверяем, прошло ли достаточно времени с последней проверки
	if !uc.lastCheck.IsZero() && time.Since(uc.lastCheck) < uc.checkInterval {
		return nil, nil
	}
	
	// Проверяем наличие обновлений
	updateInfo, err := uc.CheckForUpdates()
	if err != nil {
		return nil, err
	}
	
	// Если обновлений нет, возвращаем nil
	if updateInfo == nil {
		return nil, nil
	}
	
	// Если обновление обязательно, применяем его
	if updateInfo.Mandatory {
		uc.logger.Printf("Применение обязательного обновления до версии %s", updateInfo.Version)
		
		// Загружаем обновление
		updateFile, err := uc.DownloadUpdate(updateInfo)
		if err != nil {
			return updateInfo, fmt.Errorf("ошибка загрузки обновления: %v", err)
		}
		
		// Применяем обновление
		err = uc.ApplyUpdate(updateFile)
		if err != nil {
			return updateInfo, fmt.Errorf("ошибка применения обновления: %v", err)
		}
		
		uc.logger.Printf("Обязательное обновление до версии %s применено", updateInfo.Version)
	}
	
	return updateInfo, nil
}

// GetLatestVersion получает последнюю версию из API
func (uc *UpdateChecker) GetLatestVersion() (string, error) {
	url := fmt.Sprintf("%s/updates/latest?channel=%s&os=%s&arch=%s", 
		uc.apiEndpoint, uc.updateChannel, runtime.GOOS, runtime.GOARCH)
	
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	
	resp, err := client.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	
	var result map[string]interface{}
	err = json.Unmarshal(body, &result)
	if err != nil {
		return "", err
	}
	
	if version, ok := result["version"].(string); ok {
		return version, nil
	}
	
	return "", fmt.Errorf("неверный формат ответа")
}

// SetCheckInterval устанавливает интервал проверки обновлений
func (uc *UpdateChecker) SetCheckInterval(interval time.Duration) {
	uc.checkInterval = interval
}

// GetLastCheckTime возвращает время последней проверки обновлений
func (uc *UpdateChecker) GetLastCheckTime() time.Time {
	return uc.lastCheck
}

// IsUpdateAvailable проверяет, доступно ли обновление
func (uc *UpdateChecker) IsUpdateAvailable() (bool, error) {
	updateInfo, err := uc.CheckForUpdates()
	if err != nil {
		return false, err
	}
	
	return updateInfo != nil, nil
}

// GetUpdateNotes возвращает заметки к обновлению
func (uc *UpdateChecker) GetUpdateNotes(version string) (string, error) {
	url := fmt.Sprintf("%s/updates/notes?version=%s", uc.apiEndpoint, version)
	
	client := &http.Client{
		Timeout: 30 * time.Second,
	}
	
	resp, err := client.Get(url)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("сервер вернул код %d", resp.StatusCode)
	}
	
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	
	return string(body), nil
}

// RestartApplication перезапускает приложение после обновления
func (uc *UpdateChecker) RestartApplication() error {
	// Получаем путь к текущему исполняемому файлу
	execPath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("ошибка получения пути к исполняемому файлу: %v", err)
	}
	
	// Запускаем новый экземпляр
	cmd := exec.Command(execPath)
	cmd.Start()
	
	// Завершаем текущий процесс
	os.Exit(0)
	
	return nil
}