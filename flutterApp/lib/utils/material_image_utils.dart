/// Shared helpers for mapping material/brand names to asset image paths.
library;

/// Returns the AppImages asset path for a material name (loose match).
String? matImagePath(String name) {
  final n = name.toLowerCase();
  if (n.contains('cement block') || n.contains('concrete block') || n.contains('hollow')) return 'AppImages/materials/cementBlock.png';
  if (n.contains('cement'))       return 'AppImages/materials/cement.png';
  if (n.contains('sand'))         return 'AppImages/materials/sand.png';
  if (n.contains('aggregate'))    return 'AppImages/materials/aggregates.png';
  if (n.contains('steel') || n.contains('rebar') || n.contains('lintel')) return 'AppImages/materials/steels.png';
  if (n.contains('binding wire')) return 'AppImages/materials/bindingWire.png';
  if (n.contains('nail'))         return 'AppImages/materials/nails.png';
  if (n.contains('tile') || n.contains('skirting')) return 'AppImages/materials/tile.png';
  if (n.contains('paint'))        return 'AppImages/materials/wallPaint.png';
  if (n.contains('primer') || n.contains('filler')) return 'AppImages/materials/fillerPaints.png';
  if (n.contains('putty') || n.contains('puty'))    return 'AppImages/materials/puty.png';
  if (n.contains('brick'))        return 'AppImages/materials/brick.png';
  if (n.contains('block'))        return 'AppImages/materials/cementBlock.png';
  return null;
}

/// Returns the AppImages asset path for a brand name (loose match).
String? brandLogoPath(String brand) {
  final b = brand.toLowerCase();
  if (b.contains('causeway'))                         return 'AppImages/brands/causewayPaints.png';
  if (b.contains('dulux'))                            return 'AppImages/brands/duluxPaints.png';
  if (b.contains('lanwa'))                            return 'AppImages/brands/lanwaCement.png';
  if (b.contains('robbialac') || b.contains('robialac')) return 'AppImages/brands/robbialacPaints.png';
  if (b.contains('sanstha'))                          return 'AppImages/brands/sansthaCement.png';
  if (b.contains('taian') || b.contains('taiian'))    return 'AppImages/brands/taianSteels.png';
  return null;
}
