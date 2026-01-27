#include <Windows.h>
#include "pch.h"
const wchar_t* flag = L"flag{the_Security_level_of_HonkaiStarRail_is_???}";
class HelloFlag {
public:
	static void ShowMessage() {
		MessageBox(nullptr, flag, L"Message", MB_OK);
	}
	HelloFlag() = default;
};
BOOL APIENTRY DllMain(HMODULE hModule,
	DWORD ulReasonForCall,
	LPVOID lpReserved) {
	switch (ulReasonForCall) {
	case DLL_PROCESS_ATTACH:
	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
	case DLL_PROCESS_DETACH:
		break;
	}
	return TRUE;
}
__declspec(dllexport) void ShowFlag() {
	HelloFlag::ShowMessage();
}