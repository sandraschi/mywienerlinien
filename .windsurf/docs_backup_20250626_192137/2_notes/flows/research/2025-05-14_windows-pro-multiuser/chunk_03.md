# Legal, Licensing, and Risks

## Microsoft Licensing (EULA)
- Windows 11 Pro is licensed for single-user, single-session use.
- The EULA typically allows the *primary user* to access their session remotely, but does NOT allow multiple simultaneous sessions.
- Multi-user access (like Terminal Server/RDS) is only licensed on Windows Server with appropriate RDS CALs (Client Access Licenses).
- Modifying Windows (e.g., patching termsrv.dll or using RDP Wrapper to enable multiple sessions) is a violation of the EULA and may breach copyright law.

## Risks
- **Audit Penalties:** If discovered (e.g., during a Microsoft audit), organizations may face steep penalties, forced compliance, and retroactive licensing costs.
- **Software Instability:** System file patching can cause instability, break updates, or result in boot failures.
- **Security:** Third-party tools and patches may introduce vulnerabilities or malware.
- **Office/Third-Party Apps:** Many apps (including Microsoft Office) require proper licensing for each user/session. Volume licensing may be required.

## Community/Expert Warnings
- Most reputable IT sites and forums warn that these hacks are licensing violations.
- Some platforms (e.g., Experts-Exchange) ban discussion of such hacks for legal reasons.
- Proceeding is "at your own risk" and not supported by Microsoft.

---

Next chunk: Alternatives to patching (legal multi-user solutions).
