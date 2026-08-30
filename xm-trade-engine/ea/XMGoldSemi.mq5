// Gold 半自動: アジアレンジをロックし、ARM された日だけロンドン OCO を置く。
// 方向は選ばない。グリッド／ナンピンは実装しない。時間は TimeGMT()。

#property copyright "xm-trade-engine"
#property version   "1.00"
#property description "XM GOLD semi-auto: Asian range, London OCO, ARM from commander.json"

#include <Trade/Trade.mqh>

input group "Commander"
input string CommanderURL = "";
input string CommanderAuthHeader = "";
input bool   FailClosedOnFetchError = true;
input int    CommanderPollSeconds = 60;

input group "Risk"
input int    MagicNumber = 260831;
input double RiskPercent = 0.5;
input double MaxLot = 0.10;
input double MinLot = 0.01;
input int    MaxDailyLossPct = 2;
input double MaxSpreadPrice = 0.80;

input group "Gold London (UTC)"
input int    AsiaStartUtc = 0;
input int    AsiaEndUtc = 7;
input int    LondonStartUtc = 7;
input int    LondonEndUtc = 11;
input int    DailyAtrPeriod = 14;
input int    AtrPeriod = 14;
input double MinRangeAtrFrac = 0.15;
input double MaxRangeAtrFrac = 0.70;
input double BreakoutBufferAtr = 0.15;
input double SlAtr = 1.2;
input double RewardMultiple = 1.8;
input bool   SkipFirstFriday = true;

CTrade trade;
int hAtr = INVALID_HANDLE;
int hDailyAtr = INVALID_HANDLE;
string gCommand = "PAPER_ONLY";
string gGoldArm = "IDLE";
string gGoldArmDate = "";
datetime gLastFetch = 0;
double gDayStartEquity = 0;
int gDayStamp = 0;
double gAsiaHigh = 0;
double gAsiaLow = 0;
bool gAsiaLocked = false;
bool gPlacedToday = false;

int OnInit()
{
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(50);
   hAtr = iATR(_Symbol, PERIOD_M15, AtrPeriod);
   hDailyAtr = iATR(_Symbol, PERIOD_D1, DailyAtrPeriod);
   if(hAtr == INVALID_HANDLE || hDailyAtr == INVALID_HANDLE)
      return INIT_FAILED;
   gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   gDayStamp = DayStampGmt();
   Print("XMGoldSemi init");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(hAtr != INVALID_HANDLE) IndicatorRelease(hAtr);
   if(hDailyAtr != INVALID_HANDLE) IndicatorRelease(hDailyAtr);
}

void OnTick()
{
   if(DayStampGmt() != gDayStamp)
   {
      gDayStamp = DayStampGmt();
      gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      gAsiaLocked = false;
      gPlacedToday = false;
      gAsiaHigh = 0;
      gAsiaLow = 0;
   }

   PollCommander();
   if(DailyLossHit() || gCommand == "HALT")
   {
      CancelPendings();
      CloseMagic("halt");
      return;
   }

   MqlDateTime gmt;
   TimeToStruct(TimeGMT(), gmt);
   if(gmt.day_of_week == 0 || gmt.day_of_week == 6)
      return;
   if(SkipFirstFriday && gmt.day_of_week == 5 && gmt.day <= 7)
      return;

   if(!gAsiaLocked && gmt.hour >= AsiaEndUtc)
      LockAsiaRange();

   ManageOcoFill();

   if(!gAsiaLocked || gPlacedToday)
      return;
   if(gmt.hour < LondonStartUtc || gmt.hour >= LondonEndUtc)
   {
      if(gmt.hour >= LondonEndUtc)
         CancelPendings();
      return;
   }
   if(gGoldArm != "ARM" || gGoldArmDate != GmtDateStr())
      return;
   if(!AllowRealOrDemo())
      return;

   double spread = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(spread > MaxSpreadPrice)
      return;

   PlaceOco();
}

void LockAsiaRange()
{
   datetime start = GmtOfUtcHour(AsiaStartUtc);
   datetime end = GmtOfUtcHour(AsiaEndUtc);
   gAsiaHigh = 0;
   gAsiaLow = 0;
   int bars = iBars(_Symbol, PERIOD_M15);
   bool any = false;
   for(int i = 1; i < bars && i < 96; i++)
   {
      datetime t = BarGmt(iTime(_Symbol, PERIOD_M15, i));
      if(t < start) break;
      if(t >= end) continue;
      double h = iHigh(_Symbol, PERIOD_M15, i);
      double l = iLow(_Symbol, PERIOD_M15, i);
      if(!any)
      {
         gAsiaHigh = h;
         gAsiaLow = l;
         any = true;
      }
      else
      {
         if(h > gAsiaHigh) gAsiaHigh = h;
         if(l < gAsiaLow) gAsiaLow = l;
      }
   }
   if(!any || gAsiaHigh <= gAsiaLow)
      return;
   double dailyAtr, atr;
   if(!Copy1(hDailyAtr, 1, dailyAtr) || !Copy1(hAtr, 1, atr) || dailyAtr <= 0 || atr <= 0)
      return;
   double range = gAsiaHigh - gAsiaLow;
   double frac = range / dailyAtr;
   if(frac < MinRangeAtrFrac || frac > MaxRangeAtrFrac)
      return;
   gAsiaLocked = true;
   Print("asia locked high=", gAsiaHigh, " low=", gAsiaLow, " frac=", frac);
}

void PlaceOco()
{
   double atr;
   if(!Copy1(hAtr, 1, atr) || atr <= 0)
      return;
   double buffer = atr * BreakoutBufferAtr;
   double slDist = atr * SlAtr;
   double tpDist = slDist * RewardMultiple;
   double buy = gAsiaHigh + buffer;
   double sell = gAsiaLow - buffer;
   double lotBuy = LotFromRisk(buy, buy - slDist);
   double lotSell = LotFromRisk(sell, sell + slDist);
   if(lotBuy < MinLot || lotSell < MinLot)
      return;
   trade.BuyStop(lotBuy, buy, _Symbol, buy - slDist, buy + tpDist, ORDER_TIME_GTC, 0, "xmge-gold");
   trade.SellStop(lotSell, sell, _Symbol, sell + slDist, sell - tpDist, ORDER_TIME_GTC, 0, "xmge-gold");
   gPlacedToday = true;
}

void ManageOcoFill()
{
   bool hasPos = false;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      hasPos = true;
      break;
   }
   if(hasPos)
      CancelPendings();
}

void CancelPendings()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      trade.OrderDelete(ticket);
   }
}

void CloseMagic(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      trade.PositionClose(ticket);
      Print("close ", reason);
   }
}

double LotFromRisk(double price, double sl)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double slDist = MathAbs(price - sl);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(slDist <= 0 || equity <= 0 || tickSize <= 0 || tickValue <= 0)
      return 0;
   double lossPerLot = (slDist / tickSize) * tickValue;
   if(lossPerLot <= 0) return 0;
   double lot = (equity * (RiskPercent / 100.0)) / lossPerLot;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0) step = 0.01;
   lot = MathFloor(lot / step) * step;
   if(lot > MaxLot) lot = MaxLot;
   return lot;
}

bool AllowRealOrDemo()
{
   long mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(mode == ACCOUNT_TRADE_MODE_REAL)
      return gCommand == "RESUME";
   return true;
}

bool DailyLossHit()
{
   if(gDayStartEquity <= 0) return false;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   return ((gDayStartEquity - eq) / gDayStartEquity) * 100.0 >= MaxDailyLossPct;
}

bool Copy1(int handle, int shift, double &out)
{
   double buf[];
   if(CopyBuffer(handle, 0, shift, 1, buf) < 1) return false;
   out = buf[0];
   return MathIsValidNumber(out);
}

int DayStampGmt()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return dt.year * 10000 + dt.mon * 100 + dt.day;
}

string GmtDateStr()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return StringFormat("%04d-%02d-%02d", dt.year, dt.mon, dt.day);
}

datetime BarGmt(datetime serverTime)
{
   return serverTime + (TimeGMT() - TimeCurrent());
}

datetime GmtOfUtcHour(int hour)
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   dt.hour = hour;
   dt.min = 0;
   dt.sec = 0;
   return StructToTime(dt);
}

void PollCommander()
{
   if(StringLen(CommanderURL) == 0)
      return;
   datetime now = TimeGMT();
   if(gLastFetch != 0 && now - gLastFetch < CommanderPollSeconds)
      return;
   gLastFetch = now;
   string json = FetchJson();
   if(json == "")
   {
      if(FailClosedOnFetchError)
      {
         gCommand = "HALT";
         gGoldArm = "IDLE";
      }
      return;
   }
   string cmd = ExtractJsonString(json, "command");
   StringToUpper(cmd);
   if(cmd == "HALT" || cmd == "PAPER_ONLY" || cmd == "RESUME" || cmd == "REDUCE_RISK")
      gCommand = cmd;
   string arm = ExtractJsonString(json, "gold_arm");
   StringToUpper(arm);
   if(arm == "ARM" || arm == "SKIP" || arm == "IDLE")
      gGoldArm = arm;
   gGoldArmDate = ExtractJsonString(json, "gold_arm_date");
}

string FetchJson()
{
   char post[];
   char result[];
   string resultHeaders;
   int code = WebRequest("GET", CommanderURL, CommanderAuthHeader, 5000, post, result, resultHeaders);
   if(code != 200)
   {
      Print("commander HTTP ", code);
      return "";
   }
   return CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
}

string ExtractJsonString(string json, string key)
{
   string needle = "\"" + key + "\"";
   int p = StringFind(json, needle);
   if(p < 0) return "";
   int colon = StringFind(json, ":", p);
   if(colon < 0) return "";
   int q1 = StringFind(json, "\"", colon);
   if(q1 < 0) return "";
   int q2 = StringFind(json, "\"", q1 + 1);
   if(q2 < 0) return "";
   return StringSubstr(json, q1 + 1, q2 - q1 - 1);
}
