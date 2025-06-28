# Summary, Best Practices, and References

## Summary
- Windows 11 Pro is not designed or licensed for multiple simultaneous remote desktop sessions.
- Technical workarounds exist (RDP Wrapper, termsrv.dll patching), but all violate Microsoft licensing and carry risks (instability, malware, audit penalties).
- The only fully legal and supported solution for multi-user RDP is Windows Server with RDS and proper CALs.
- Third-party solutions (GO-Global, Citrix, VMware, Parallels) offer legal multi-user remote access, but at a cost.

## Best Practices
- **For home/lab use:** Understand the risks before experimenting. Never use in production or business settings.
- **For business/production:** Always use licensed, supported solutions (Windows Server + RDS, or a third-party platform).
- **Security:** Avoid downloading patches from unknown sources. Monitor for malware and vulnerabilities.
- **Licensing:** Ensure you have the correct licenses for Windows, RDS, and any installed software (e.g., Microsoft Office).

## References
- [RDP Wrapper GitHub](https://github.com/stascorp/rdpwrap)
- [How to Allow Multiple RDP Sessions (woshub.com)](https://woshub.com/how-to-allow-multiple-rdp-sessions-in-windows-10/)
- [Microsoft EULA](https://www.microsoft.com/en-us/useterms)
- [GO-Global Pricing](https://www.graphon.com/pricing)
- [Citrix Virtual Apps & Desktops](https://www.citrix.com/products/citrix-virtual-apps-and-desktops/)
- [VMware Horizon Cloud](https://www.vmware.com/products/horizon.html)
- [Parallels RAS](https://www.parallels.com/products/ras/)
- [LAN-Tech: Legal Issues](https://blog.lan-tech.ca/2013/10/31/multiple-rdp-sessions-on-a-pc-legal-or-not/)
