using Microsoft.AspNetCore.Builder;

var builder = WebApplication.CreateBuilder(args);

// Register modules
Modules.Accounts.AccountModule.Register(builder.Services);

var app = builder.Build();

// Map endpoints
Modules.Accounts.AccountModule.MapEndpoints(app);

app.Run();