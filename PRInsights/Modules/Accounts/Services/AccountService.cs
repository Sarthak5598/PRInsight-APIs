namespace PrInsights.Modules.Accounts.Services;

public interface IAccountService
{
    Task<string> CreateUser();
}

public class AccountService : IAccountService
{
    public Task<string> CreateUser()
    {
        return Task.FromResult("User Created");
    }
}