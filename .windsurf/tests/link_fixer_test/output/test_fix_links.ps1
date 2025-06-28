# Test wrapper for fix_broken_links.ps1

# Import the script as a module
. "D:\\Dev\\repos\\mywienerlinien\\.windsurf\\tests\\..\\scripts\\fix_broken_links.ps1"

# Override configuration for testing
$script:config = @{
    RootDir = 'D:\\Dev\\repos\\mywienerlinien\\.windsurf\\tests\\link_fixer_test\\output'
    LogsDir = 'D:\\Dev\\repos\\mywienerlinien\\.windsurf\\tests\\link_fixer_test\\output'
    SorryPage = '/sorry.html'
    LogFile = 'link_fix_test.log'
}

# Run the main function
Start-LinkFix
