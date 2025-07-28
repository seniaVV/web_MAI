#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <ctime>
#include <winsock2.h>
#include <io.h>
#include <fcntl.h>
#pragma comment(lib, "ws2_32.lib")

std::string reverseString(const std::string& str) {
    return std::string(str.rbegin(), str.rend());
}

std::string getCurrentTime() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time = std::chrono::system_clock::to_time_t(now);
    char buf[100];
    ctime_s(buf, sizeof(buf), &now_time);
    std::string timeStr(buf);
    timeStr.erase(timeStr.find_last_not_of("\n") + 1);
    return timeStr;
}

void writeToLog(const std::string& message, std::ofstream& logFile) {
    logFile << "[" << getCurrentTime() << "] " << message << std::endl;
}

int main() {
    SetConsoleOutputCP(CP_UTF8);
    SetConsoleCP(CP_UTF8);

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "Ошибка инициализации Winsock" << std::endl;
        return 1;
    }

    SOCKET serverSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (serverSocket == INVALID_SOCKET) {
        std::cerr << "Ошибка создания сокета" << std::endl;
        WSACleanup();
        return 1;
    }

    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(12345);

    if (bind(serverSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << "Ошибка привязки сокета" << std::endl;
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    if (listen(serverSocket, 1) == SOCKET_ERROR) {
        std::cerr << "Ошибка перехода в режим прослушивания" << std::endl;
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    std::ofstream logFile("server_log.txt", std::ios::app);
    if (!logFile.is_open()) {
        std::cerr << "Ошибка открытия лог-файла" << std::endl;
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    writeToLog("Сервер запущен", logFile);
    std::cout << "Сервер ожидает подключения..." << std::endl;

    while (true) {
        sockaddr_in clientAddr;
        int clientAddrSize = sizeof(clientAddr);
        SOCKET clientSocket = accept(serverSocket, (sockaddr*)&clientAddr, &clientAddrSize);
        if (clientSocket == INVALID_SOCKET) {
            writeToLog("Ошибка принятия подключения", logFile);
            closesocket(serverSocket);
            WSACleanup();
            logFile.close();
            return 1;
        }

        char clientIP[16];
        const char* ip = inet_ntoa(clientAddr.sin_addr);
        if (ip != nullptr) {
            strncpy(clientIP, ip, sizeof(clientIP));
            writeToLog("Подключен клиент: " + std::string(clientIP), logFile);
        } else {
            writeToLog("Подключен клиент (не удалось получить IP)", logFile);
        }

        char buffer[1024];
        int bytesReceived = recv(clientSocket, buffer, sizeof(buffer), 0);
        if (bytesReceived == SOCKET_ERROR) {
            writeToLog("Ошибка получения данных", logFile);
        } 
        buffer[bytesReceived] = '\0';
        std::string clientMessage(buffer);
        writeToLog("Получено сообщение: " + clientMessage, logFile);

        Sleep(2000);

        std::string reversedMessage = reverseString(clientMessage);
        std::string response = reversedMessage + ". Server is written by Korkina K.V. M3O-107BV-24";
        
        send(clientSocket, response.c_str(), response.size(), 0);
        writeToLog("Отправлен ответ: " + response, logFile);

        Sleep(5000);

        closesocket(clientSocket);
        writeToLog("Соединение с клиентом закрыто", logFile);
    }
    
    closesocket(serverSocket);
    WSACleanup();
    logFile.close();

    return 0;
}
