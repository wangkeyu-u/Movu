import { execFileSync } from "node:child_process";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const apiBase = process.env.MOVU_API_URL ?? "http://127.0.0.1:8000/api";
const adminAppUrl = process.env.MOVU_ADMIN_APP_URL ?? "http://127.0.0.1:6173";
const password = "StrongPass123";

interface UserRead {
  user_id: number;
  email: string;
  verification_status: string;
  email_verified: boolean;
}

interface AuthResponse {
  access_token: string;
  user: UserRead;
}

interface VehicleRead {
  vehicle_id: number;
  verification_status: string;
}

interface TripRead {
  trip_id: number;
  driver_id: number;
  status: string;
}

interface RideRequestRead {
  request_id: number;
  status: string;
}

interface MatchRead {
  match_id: number;
  trip_id: number;
  request_id: number;
  status: string;
}

interface AuditLogRead {
  action: string;
  entity_type: string;
  entity_id: string;
}

async function post<T>(request: APIRequestContext, path: string, token: string | null, data: unknown, expectedStatus = 200): Promise<T> {
  const response = await request.post(`${apiBase}${path}`, {
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });
  expect(response.status(), `${path} response`).toBe(expectedStatus);
  return response.json() as Promise<T>;
}

async function get<T>(request: APIRequestContext, path: string, token: string, expectedStatus = 200): Promise<T> {
  const response = await request.get(`${apiBase}${path}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  expect(response.status(), `${path} response`).toBe(expectedStatus);
  return response.json() as Promise<T>;
}

async function patch<T>(request: APIRequestContext, path: string, token: string, data: unknown, expectedStatus = 200): Promise<T> {
  const response = await request.patch(`${apiBase}${path}`, {
    data,
    headers: { Authorization: `Bearer ${token}` }
  });
  expect(response.status(), `${path} response`).toBe(expectedStatus);
  return response.json() as Promise<T>;
}

async function login(request: APIRequestContext, email: string, loginPassword = password): Promise<AuthResponse> {
  return post<AuthResponse>(request, "/auth/login", null, { email, password: loginPassword });
}

async function expectPostError(
  request: APIRequestContext,
  path: string,
  token: string | null,
  data: unknown,
  expectedStatus: number,
  detail: string
) {
  const response = await request.post(`${apiBase}${path}`, {
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });
  expect(response.status()).toBe(expectedStatus);
  await expect(response.json()).resolves.toMatchObject({ detail });
}

async function readVerificationToken(email: string): Promise<string> {
  const escapedEmail = email.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const tokenPattern = new RegExp(`\\[email skipped\\] to=${escapedEmail}[\\s\\S]*?verify-email\\?token=([A-Za-z0-9_-]+)`, "g");
  const deadline = Date.now() + 20_000;

  while (Date.now() < deadline) {
    const logs = execFileSync("docker", ["compose", "logs", "--no-color", "backend"], { encoding: "utf8" });
    let match: RegExpExecArray | null;
    let latestToken: string | null = null;
    while ((match = tokenPattern.exec(logs))) {
      latestToken = match[1];
    }
    if (latestToken) return latestToken;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error(`Could not find verification token in backend logs for ${email}`);
}

async function verifyEmailFromBackendLogs(request: APIRequestContext, email: string): Promise<UserRead> {
  const token = await readVerificationToken(email);
  return post<UserRead>(request, "/auth/verify-email", null, { token });
}

async function loginAdminUi(page: Page) {
  await page.goto(adminAppUrl);
  await page.getByLabel("Email").fill("admin@taylors.edu.my");
  await page.getByLabel("Password").fill("Password123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: /Operations overview|Users/ })).toBeVisible();
}

test("real rider-driver approval, match, safety, rating, and audit flow", async ({ browser, page, request }) => {
  const runId = Date.now().toString(36);
  const riderEmail = `e2e-rider-${runId}@sd.taylors.edu.my`;
  const driverEmail = `e2e-driver-${runId}@sd.taylors.edu.my`;

  let rider: UserRead;
  let driver: UserRead;
  let riderToken: string;
  let driverToken: string;
  let adminToken: string;
  let vehicle: VehicleRead;
  let trip: TripRead;

  await test.step("new accounts require email verification before login", async () => {
    rider = await post<UserRead>(
      request,
      "/auth/register",
      null,
      {
        name: "E2E Rider",
        email: riderEmail,
        student_id: `E2ER${runId}`,
        password,
        role: "rider",
        gender: "female"
      },
      201
    );
    driver = await post<UserRead>(
      request,
      "/auth/register",
      null,
      {
        name: "E2E Driver",
        email: driverEmail,
        student_id: `E2ED${runId}`,
        password,
        role: "driver",
        gender: "male"
      },
      201
    );

    await expectPostError(request, "/auth/login", null, { email: riderEmail, password }, 403, "Email is not verified");

    const verifiedRider = await verifyEmailFromBackendLogs(request, riderEmail);
    const verifiedDriver = await verifyEmailFromBackendLogs(request, driverEmail);
    expect(verifiedRider).toMatchObject({ email: riderEmail, email_verified: true, verification_status: "pending" });
    expect(verifiedDriver).toMatchObject({ email: driverEmail, email_verified: true, verification_status: "pending" });
  });

  await test.step("pending user app clearly locks core actions", async () => {
    await page.goto("/");
    await page.getByLabel("Campus email").fill(riderEmail);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText("Your account is waiting for admin approval")).toBeVisible();
    await expect(page.getByText("Request a ride")).toBeHidden();

    const auth = await login(request, riderEmail);
    riderToken = auth.access_token;
    const pendingDriverAuth = await login(request, driverEmail);
    await expectPostError(
      request,
      "/ride-requests",
      riderToken,
      {
        origin: "Taylor's Lakeside Campus",
        destination: "Sunway Pyramid",
        preferred_time: new Date(Date.now() + 90 * 60_000).toISOString(),
        passenger_count: 1,
        gender_preference: "none"
      },
      403,
      "Account is not approved"
    );
    await expectPostError(
      request,
      "/vehicles",
      pendingDriverAuth.access_token,
      {
        plate_number: `PEND${runId}`.slice(0, 12).toUpperCase(),
        vehicle_model: "Perodua Myvi",
        seat_count: 4
      },
      403,
      "Account is not approved"
    );
  });

  await test.step("admin dashboard shows pending user and approval state", async () => {
    const adminAuth = await login(request, "admin@taylors.edu.my", "Password123");
    adminToken = adminAuth.access_token;

    const adminPage = await browser.newPage();
    await loginAdminUi(adminPage);
    await adminPage.getByRole("link", { name: "Users" }).click();
    const riderRow = adminPage.locator("tr").filter({ hasText: riderEmail });
    await expect(riderRow).toContainText("Pending");

    await patch<UserRead>(request, `/users/${rider.user_id}/verification`, adminToken, { verification_status: "approved" });
    await patch<UserRead>(request, `/users/${driver.user_id}/verification`, adminToken, { verification_status: "approved" });

    await adminPage.reload();
    await expect(adminPage.locator("tr").filter({ hasText: riderEmail })).toContainText("Approved");
    await adminPage.close();

    await page.reload();
    await expect(page.getByText("Request a ride")).toBeVisible();
  });

  await test.step("approved driver still needs approved vehicle before posting trip", async () => {
    const driverAuth = await login(request, driverEmail);
    driverToken = driverAuth.access_token;
    const departureTime = new Date(Date.now() + 90 * 60_000).toISOString();

    await expectPostError(
      request,
      "/trips",
      driverToken,
      {
        origin: "Taylor's Lakeside Campus",
        destination: "Sunway Pyramid",
        departure_time: departureTime,
        available_seats: 4
      },
      403,
      "Driver must have an approved vehicle before creating trips"
    );

    vehicle = await post<VehicleRead>(
      request,
      "/vehicles",
      driverToken,
      {
        plate_number: `E2E${runId}`.slice(0, 12).toUpperCase(),
        vehicle_model: "Perodua Myvi",
        seat_count: 4
      },
      201
    );
    expect(vehicle.verification_status).toBe("pending");

    await expectPostError(
      request,
      "/trips",
      driverToken,
      {
        origin: "Taylor's Lakeside Campus",
        destination: "Sunway Pyramid",
        departure_time: departureTime,
        available_seats: 4
      },
      403,
      "Driver must have an approved vehicle before creating trips"
    );

    vehicle = await patch<VehicleRead>(request, `/vehicles/${vehicle.vehicle_id}/verification`, adminToken, { verification_status: "approved" });
    expect(vehicle.verification_status).toBe("approved");

    trip = await post<TripRead>(
      request,
      "/trips",
      driverToken,
      {
        origin: "Taylor's Lakeside Campus",
        destination: "Sunway Pyramid",
        departure_time: departureTime,
        available_seats: 4
      },
      201
    );
    expect(trip).toMatchObject({ driver_id: driver.user_id, status: "posted" });
  });

  await test.step("approved rider creates request, confirms match, then enters safety flow", async () => {
    const preferredTime = new Date(Date.now() + 95 * 60_000).toISOString();
    const rideRequest = await post<RideRequestRead>(
      request,
      "/ride-requests",
      riderToken,
      {
        origin: "Taylor's Lakeside Campus",
        destination: "Sunway Pyramid",
        preferred_time: preferredTime,
        passenger_count: 1,
        gender_preference: "none"
      },
      201
    );
    expect(rideRequest.status).toBe("pending");

    const recommendations = await get<MatchRead[]>(request, `/matches/ride-requests/${rideRequest.request_id}/recommendations`, riderToken);
    const match = recommendations.find((candidate) => candidate.trip_id === trip.trip_id);
    expect(match, "newly posted driver trip should be recommended").toBeTruthy();

    const confirmedMatch = await post<MatchRead>(request, `/matches/${match!.match_id}/confirm`, riderToken, {}, 200);
    expect(confirmedMatch).toMatchObject({ status: "confirmed", request_id: rideRequest.request_id, trip_id: trip.trip_id });

    trip = await patch<TripRead>(request, `/trips/${trip.trip_id}/status`, driverToken, { status: "ongoing" });
    expect(trip.status).toBe("ongoing");

    const location = await post<{ user_id: number; trip_id: number }>(
      request,
      "/locations",
      driverToken,
      { trip_id: trip.trip_id, latitude: 3.0646, longitude: 101.6159 },
      201
    );
    expect(location).toMatchObject({ user_id: driver.user_id, trip_id: trip.trip_id });

    const latest = await get<{ user_id: number; trip_id: number }>(request, `/locations/trips/${trip.trip_id}/latest`, riderToken);
    expect(latest).toMatchObject({ user_id: driver.user_id, trip_id: trip.trip_id });

    const sos = await post<{ sos_id: number; status: string }>(
      request,
      "/sos",
      riderToken,
      { trip_id: trip.trip_id, latitude: 3.0646, longitude: 101.6159 },
      201
    );
    expect(sos.status).toBe("new");

    const resolvedSos = await patch<{ status: string }>(request, `/sos/${sos.sos_id}/status`, adminToken, { status: "resolved" });
    expect(resolvedSos.status).toBe("resolved");

    trip = await patch<TripRead>(request, `/trips/${trip.trip_id}/status`, driverToken, { status: "completed" });
    expect(trip.status).toBe("completed");

    const rating = await post<{ score: number; to_user_id: number }>(
      request,
      "/reports/ratings",
      riderToken,
      { to_user_id: driver.user_id, trip_id: trip.trip_id, score: 5, comment: "Smooth verified E2E ride" },
      201
    );
    expect(rating).toMatchObject({ score: 5, to_user_id: driver.user_id });
  });

  await test.step("admin audit log records security-sensitive operations", async () => {
    const auditLogs = await get<AuditLogRead[]>(request, "/admin/audit-logs", adminToken);
    expect(auditLogs).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ action: "user.verification_updated", entity_type: "user", entity_id: String(rider.user_id) }),
        expect.objectContaining({ action: "user.verification_updated", entity_type: "user", entity_id: String(driver.user_id) }),
        expect.objectContaining({ action: "vehicle.verification_updated", entity_type: "vehicle", entity_id: String(vehicle.vehicle_id) }),
        expect.objectContaining({ action: "sos.status_updated", entity_type: "sos_event" })
      ])
    );
  });
});
