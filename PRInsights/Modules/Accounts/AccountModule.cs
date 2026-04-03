using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using PrInsights.Modules.Accounts.Services;

namespace Modules.Accounts;

public static class AccountModule
{
    public static void Register(IServiceCollection services)
    {
        services.AddScoped<IAccountService, AccountService>();
    }

    public static void MapEndpoints(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/accounts");

        group.MapPost("/", async (IAccountService service) =>
        {
            return await service.CreateUser();
        });
    }
}